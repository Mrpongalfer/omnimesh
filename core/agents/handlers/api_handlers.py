"""
API Handler module for Agent Ex-Work v3.0
UMCC Genesis Agent - External API and Data Fetching Handler

Specialized handler for external API interactions, data fetching operations,
and integration with third-party services while maintaining UMCC security
protocols and autonomous operation capabilities.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse
import aiohttp
import aiofiles
from pathlib import Path
import ssl
import certifi

from .base_handler import BaseHandler, HandlerContext
from ..models.action import ActionType
from ..models.results import ActionResult


class APIHandler(BaseHandler):
    """
    Handler for external API calls and data fetching operations.
    
    Supports REST API interactions, GraphQL queries, webhook management,
    and secure data retrieval with comprehensive error handling and
    retry mechanisms suitable for autonomous operation.
    """
    
    SUPPORTED_ACTIONS = {
        ActionType.CALL_EXTERNAL_API,
        ActionType.FETCH_DATA,
        ActionType.HTTP_REQUEST
    }
    
    def __init__(self):
        super().__init__("api_handler")
        
        # API configuration defaults
        self.default_timeout = 30
        self.max_retries = 3
        self.retry_delay = 1.0
        self.max_response_size = 10 * 1024 * 1024  # 10MB
        
        # Security configuration
        self.allowed_domains = set()  # Will be populated from config
        self.blocked_domains = set()
        self.require_https = True
        self.verify_ssl = True
        
        # Rate limiting
        self.rate_limits = {}
        self.request_counts = {}
        
        # Response caching
        self.cache_enabled = True
        self.cache_ttl = 300  # 5 minutes default
        self.response_cache = {}
        
        # Headers and authentication
        self.default_headers = {
            "User-Agent": "UMCC-Agent/3.0 (Autonomous System)",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        
        # SSL context for secure connections
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        self.logger.info("API Handler initialized with security protocols")
    
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if this handler supports the given action type"""
        return action_type in self.SUPPORTED_ACTIONS
    
    async def execute(self, context: HandlerContext) -> ActionResult:
        """
        Execute API-based actions with comprehensive security and error handling.
        
        Args:
            context: Execution context containing action and environment
            
        Returns:
            ActionResult with API response and metadata
        """
        action_type = context.action.action_type
        
        # Route to specific API operation
        if action_type == ActionType.CALL_EXTERNAL_API:
            return await self._handle_external_api_call(context)
        elif action_type == ActionType.FETCH_DATA:
            return await self._handle_data_fetch(context)
        elif action_type == ActionType.HTTP_REQUEST:
            return await self._handle_http_request(context)
        else:
            raise ValueError(f"Unsupported action type: {action_type}")
    
    async def _handle_external_api_call(self, context: HandlerContext) -> ActionResult:
        """
        Handle structured external API calls with authentication and validation.
        
        Args:
            context: Execution context
            
        Returns:
            ActionResult with API response
        """
        params = context.action.parameters
        
        # Extract API parameters
        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        data = params.get("data")
        json_data = params.get("json")
        auth = params.get("auth", {})
        timeout = params.get("timeout", self.default_timeout)
        
        if not url:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No URL provided for external API call"
            )
        
        # Security validation
        security_check = self._validate_api_security(url, context)
        if not security_check["allowed"]:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"API call blocked: {security_check['reason']}"
            )
        
        context.add_audit_entry(f"External API call initiated: {method} {url}")
        
        try:
            # Prepare headers with authentication
            request_headers = self._prepare_headers(headers, auth)
            
            # Execute API call with retries
            response_data = await self._execute_api_request(
                url=url,
                method=method,
                headers=request_headers,
                data=data,
                json_data=json_data,
                timeout=timeout,
                context=context
            )
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output=response_data,
                metadata={
                    "url": url,
                    "method": method,
                    "status_code": response_data.get("status_code"),
                    "response_size": len(str(response_data.get("content", ""))),
                    "duration": response_data.get("duration"),
                    "cached": response_data.get("cached", False)
                }
            )
            
        except Exception as e:
            self.logger.error(f"External API call failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"External API call failed: {str(e)}"
            )
    
    async def _handle_data_fetch(self, context: HandlerContext) -> ActionResult:
        """
        Handle specialized data fetching operations with format parsing.
        
        Args:
            context: Execution context
            
        Returns:
            ActionResult with fetched and parsed data
        """
        params = context.action.parameters
        
        # Extract data fetch parameters
        sources = params.get("sources", [])
        data_format = params.get("format", "json")
        filters = params.get("filters", {})
        transformations = params.get("transformations", [])
        merge_strategy = params.get("merge_strategy", "append")
        
        if not sources:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No data sources provided for fetch operation"
            )
        
        context.add_audit_entry(f"Data fetch initiated: {len(sources)} sources")
        
        try:
            # Fetch data from all sources
            fetched_data = []
            fetch_metadata = []
            
            for source in sources:
                if isinstance(source, str):
                    # Simple URL source
                    source_data = await self._fetch_single_source(
                        {"url": source, "format": data_format}, context
                    )
                else:
                    # Complex source configuration
                    source_data = await self._fetch_single_source(source, context)
                
                fetched_data.append(source_data["data"])
                fetch_metadata.append(source_data["metadata"])
            
            # Apply filters and transformations
            processed_data = self._process_fetched_data(
                fetched_data, filters, transformations, merge_strategy
            )
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output={
                    "data": processed_data,
                    "sources": len(sources),
                    "total_records": self._count_records(processed_data),
                    "format": data_format,
                    "metadata": fetch_metadata
                },
                metadata={
                    "sources_count": len(sources),
                    "format": data_format,
                    "total_size": len(str(processed_data)),
                    "processing_applied": len(transformations) > 0 or len(filters) > 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"Data fetch failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"Data fetch failed: {str(e)}"
            )
    
    async def _handle_http_request(self, context: HandlerContext) -> ActionResult:
        """
        Handle generic HTTP requests with full control over parameters.
        
        Args:
            context: Execution context
            
        Returns:
            ActionResult with HTTP response
        """
        params = context.action.parameters
        
        # Extract HTTP request parameters
        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        params_dict = params.get("params", {})
        data = params.get("data")
        json_data = params.get("json")
        files = params.get("files", {})
        cookies = params.get("cookies", {})
        allow_redirects = params.get("allow_redirects", True)
        timeout = params.get("timeout", self.default_timeout)
        
        if not url:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No URL provided for HTTP request"
            )
        
        context.add_audit_entry(f"HTTP request initiated: {method} {url}")
        
        try:
            # Execute HTTP request
            response_data = await self._execute_http_request(
                url=url,
                method=method,
                headers=headers,
                params=params_dict,
                data=data,
                json_data=json_data,
                files=files,
                cookies=cookies,
                allow_redirects=allow_redirects,
                timeout=timeout,
                context=context
            )
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output=response_data,
                metadata={
                    "url": url,
                    "method": method,
                    "status_code": response_data.get("status_code"),
                    "content_type": response_data.get("content_type"),
                    "content_length": response_data.get("content_length"),
                    "duration": response_data.get("duration")
                }
            )
            
        except Exception as e:
            self.logger.error(f"HTTP request failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"HTTP request failed: {str(e)}"
            )
    
    async def _execute_api_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        data: Any = None,
        json_data: Any = None,
        timeout: int = None,
        context: HandlerContext = None
    ) -> Dict[str, Any]:
        """
        Execute an API request with retry logic and caching.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            data: Request body data
            json_data: JSON request data
            timeout: Request timeout
            context: Execution context
            
        Returns:
            Dictionary containing response data and metadata
        """
        timeout = timeout or self.default_timeout
        
        # Check cache first
        cache_key = self._generate_cache_key(url, method, headers, data, json_data)
        if self.cache_enabled and method == "GET":
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self.logger.debug(f"Returning cached response for {url}")
                return cached_response
        
        # Rate limiting check
        if not self._check_rate_limit(url):
            raise Exception(f"Rate limit exceeded for {url}")
        
        start_time = time.time()
        
        # Execute request with retries
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    connector=aiohttp.TCPConnector(ssl=self.ssl_context)
                ) as session:
                    
                    # Prepare request kwargs
                    kwargs = {
                        "headers": headers,
                        "ssl": self.ssl_context if self.verify_ssl else False
                    }
                    
                    if data is not None:
                        kwargs["data"] = data
                    if json_data is not None:
                        kwargs["json"] = json_data
                    
                    # Execute request
                    async with session.request(method, url, **kwargs) as response:
                        
                        # Check response size
                        content_length = response.headers.get("Content-Length")
                        if content_length and int(content_length) > self.max_response_size:
                            raise Exception(f"Response too large: {content_length} bytes")
                        
                        # Read response
                        content = await response.read()
                        if len(content) > self.max_response_size:
                            raise Exception(f"Response too large: {len(content)} bytes")
                        
                        # Parse response based on content type
                        content_type = response.headers.get("Content-Type", "").lower()
                        parsed_content = self._parse_response_content(content, content_type)
                        
                        # Prepare response data
                        response_data = {
                            "status_code": response.status,
                            "headers": dict(response.headers),
                            "content": parsed_content,
                            "content_type": content_type,
                            "content_length": len(content),
                            "url": str(response.url),
                            "duration": time.time() - start_time,
                            "cached": False
                        }
                        
                        # Cache successful GET requests
                        if self.cache_enabled and method == "GET" and response.status == 200:
                            self._cache_response(cache_key, response_data)
                        
                        # Update rate limiting
                        self._update_rate_limit(url)
                        
                        return response_data
                        
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise Exception(f"Request timed out after {timeout} seconds")
                
            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise Exception(f"HTTP client error: {str(e)}")
                
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise
        
        raise Exception("Max retries exceeded")
    
    async def _execute_http_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any] = None,
        data: Any = None,
        json_data: Any = None,
        files: Dict[str, Any] = None,
        cookies: Dict[str, str] = None,
        allow_redirects: bool = True,
        timeout: int = None,
        context: HandlerContext = None
    ) -> Dict[str, Any]:
        """Execute a generic HTTP request with full parameter support"""
        
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout),
                connector=aiohttp.TCPConnector(ssl=self.ssl_context)
            ) as session:
                
                # Prepare request kwargs
                kwargs = {
                    "headers": headers,
                    "params": params,
                    "allow_redirects": allow_redirects,
                    "ssl": self.ssl_context if self.verify_ssl else False
                }
                
                if cookies:
                    kwargs["cookies"] = cookies
                if data is not None:
                    kwargs["data"] = data
                if json_data is not None:
                    kwargs["json"] = json_data
                
                # Handle file uploads
                if files:
                    form_data = aiohttp.FormData()
                    for key, file_info in files.items():
                        if isinstance(file_info, dict):
                            form_data.add_field(
                                key, 
                                file_info["content"],
                                filename=file_info.get("filename"),
                                content_type=file_info.get("content_type")
                            )
                        else:
                            form_data.add_field(key, file_info)
                    kwargs["data"] = form_data
                
                # Execute request
                async with session.request(method, url, **kwargs) as response:
                    content = await response.read()
                    content_type = response.headers.get("Content-Type", "")
                    
                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "content": self._parse_response_content(content, content_type),
                        "content_type": content_type,
                        "content_length": len(content),
                        "url": str(response.url),
                        "duration": time.time() - start_time,
                        "reason": response.reason
                    }
                    
        except Exception as e:
            raise Exception(f"HTTP request failed: {str(e)}")
    
    async def _fetch_single_source(
        self, 
        source: Dict[str, Any], 
        context: HandlerContext
    ) -> Dict[str, Any]:
        """Fetch data from a single source with format-specific parsing"""
        
        url = source.get("url", "")
        data_format = source.get("format", "json")
        headers = source.get("headers", {})
        auth = source.get("auth", {})
        
        # Execute the fetch
        request_headers = self._prepare_headers(headers, auth)
        response_data = await self._execute_api_request(
            url=url,
            method="GET",
            headers=request_headers,
            context=context
        )
        
        # Parse based on format
        parsed_data = self._parse_data_format(
            response_data["content"], data_format
        )
        
        return {
            "data": parsed_data,
            "metadata": {
                "url": url,
                "format": data_format,
                "status_code": response_data["status_code"],
                "size": response_data["content_length"],
                "duration": response_data["duration"]
            }
        }
    
    def _validate_api_security(self, url: str, context: HandlerContext) -> Dict[str, Any]:
        """Validate API call against security policies"""
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check blocked domains
        if domain in self.blocked_domains:
            return {"allowed": False, "reason": f"Domain {domain} is blocked"}
        
        # Check allowed domains (if configured)
        if self.allowed_domains and domain not in self.allowed_domains:
            return {"allowed": False, "reason": f"Domain {domain} not in allowed list"}
        
        # Check HTTPS requirement
        if self.require_https and parsed_url.scheme != "https":
            return {"allowed": False, "reason": "HTTPS required for external API calls"}
        
        # Check for private IP ranges (basic check)
        if self._is_private_ip(domain):
            security_level = context.security_level
            if security_level == "high":
                return {"allowed": False, "reason": "Private IP access blocked in high security mode"}
        
        return {"allowed": True, "reason": "Security validation passed"}
    
    def _prepare_headers(self, custom_headers: Dict[str, str], auth: Dict[str, Any]) -> Dict[str, str]:
        """Prepare request headers with authentication"""
        
        headers = self.default_headers.copy()
        headers.update(custom_headers)
        
        # Add authentication headers
        if auth:
            auth_type = auth.get("type", "").lower()
            
            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth['token']}"
            elif auth_type == "basic":
                import base64
                credentials = f"{auth['username']}:{auth['password']}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded_credentials}"
            elif auth_type == "api_key":
                key_name = auth.get("key_name", "X-API-Key")
                headers[key_name] = auth["api_key"]
            elif auth_type == "custom":
                headers.update(auth.get("headers", {}))
        
        return headers
    
    def _parse_response_content(self, content: bytes, content_type: str) -> Any:
        """Parse response content based on content type"""
        
        try:
            # Decode bytes to string
            text_content = content.decode("utf-8")
            
            # Parse based on content type
            if "application/json" in content_type:
                return json.loads(text_content)
            elif "application/xml" in content_type or "text/xml" in content_type:
                # Basic XML parsing - you might want to use a proper XML parser
                return {"xml_content": text_content}
            elif "text/" in content_type:
                return text_content
            else:
                # Return as base64 for binary content
                import base64
                return {
                    "binary_content": base64.b64encode(content).decode(),
                    "content_type": content_type
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to parse response content: {str(e)}")
            return {"raw_content": content.hex(), "parse_error": str(e)}
    
    def _parse_data_format(self, content: Any, data_format: str) -> Any:
        """Parse content based on specified data format"""
        
        if data_format.lower() == "json":
            if isinstance(content, str):
                return json.loads(content)
            return content
        elif data_format.lower() == "csv":
            # Basic CSV parsing - you might want to use pandas or csv module
            if isinstance(content, str):
                lines = content.strip().split('\n')
                if lines:
                    headers = lines[0].split(',')
                    data = []
                    for line in lines[1:]:
                        row = dict(zip(headers, line.split(',')))
                        data.append(row)
                    return data
            return content
        elif data_format.lower() == "xml":
            # Return as-is for now - implement proper XML parsing if needed
            return content
        else:
            return content
    
    def _process_fetched_data(
        self, 
        data_list: List[Any], 
        filters: Dict[str, Any], 
        transformations: List[Dict[str, Any]], 
        merge_strategy: str
    ) -> Any:
        """Process fetched data with filters and transformations"""
        
        # Apply merge strategy
        if merge_strategy == "append":
            merged_data = []
            for data in data_list:
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
        elif merge_strategy == "merge":
            merged_data = {}
            for data in data_list:
                if isinstance(data, dict):
                    merged_data.update(data)
        else:
            merged_data = data_list
        
        # Apply filters (basic implementation)
        if filters:
            merged_data = self._apply_filters(merged_data, filters)
        
        # Apply transformations (basic implementation)
        for transformation in transformations:
            merged_data = self._apply_transformation(merged_data, transformation)
        
        return merged_data
    
    def _apply_filters(self, data: Any, filters: Dict[str, Any]) -> Any:
        """Apply filters to data (basic implementation)"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated filtering
        return data
    
    def _apply_transformation(self, data: Any, transformation: Dict[str, Any]) -> Any:
        """Apply a single transformation to data (basic implementation)"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated transformations
        return data
    
    def _count_records(self, data: Any) -> int:
        """Count the number of records in processed data"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        else:
            return 0
    
    def _generate_cache_key(
        self, 
        url: str, 
        method: str, 
        headers: Dict[str, str], 
        data: Any, 
        json_data: Any
    ) -> str:
        """Generate a cache key for the request"""
        import hashlib
        
        key_components = [
            url,
            method,
            json.dumps(sorted(headers.items())),
            str(data) if data else "",
            json.dumps(json_data) if json_data else ""
        ]
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if cache_key in self.response_cache:
            cached_item = self.response_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                response = cached_item["response"].copy()
                response["cached"] = True
                return response
            else:
                # Remove expired cache entry
                del self.response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response_data: Dict[str, Any]) -> None:
        """Cache a response"""
        self.response_cache[cache_key] = {
            "response": response_data.copy(),
            "timestamp": time.time()
        }
        
        # Simple cache size management
        if len(self.response_cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self.response_cache.keys(),
                key=lambda k: self.response_cache[k]["timestamp"]
            )[:100]
            for key in oldest_keys:
                del self.response_cache[key]
    
    def _check_rate_limit(self, url: str) -> bool:
        """Check if request is within rate limits"""
        domain = urlparse(url).netloc
        current_time = time.time()
        
        if domain not in self.request_counts:
            self.request_counts[domain] = []
        
        # Remove old requests (older than 1 minute)
        self.request_counts[domain] = [
            req_time for req_time in self.request_counts[domain]
            if current_time - req_time < 60
        ]
        
        # Check rate limit (default: 60 requests per minute)
        rate_limit = self.rate_limits.get(domain, 60)
        return len(self.request_counts[domain]) < rate_limit
    
    def _update_rate_limit(self, url: str) -> None:
        """Update rate limit tracking"""
        domain = urlparse(url).netloc
        current_time = time.time()
        
        if domain not in self.request_counts:
            self.request_counts[domain] = []
        
        self.request_counts[domain].append(current_time)
    
    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname resolves to a private IP address"""
        import socket
        import ipaddress
        
        try:
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False
    
    def configure_security(self, config: Dict[str, Any]) -> None:
        """Configure security settings from configuration"""
        self.allowed_domains = set(config.get("allowed_domains", []))
        self.blocked_domains = set(config.get("blocked_domains", []))
        self.require_https = config.get("require_https", True)
        self.verify_ssl = config.get("verify_ssl", True)
        self.rate_limits.update(config.get("rate_limits", {}))
        
        self.logger.info(f"Security configuration updated: {len(self.allowed_domains)} allowed domains, {len(self.blocked_domains)} blocked domains")
