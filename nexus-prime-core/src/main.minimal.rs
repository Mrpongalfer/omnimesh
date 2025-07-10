// Simplified main.rs for nexus-prime-core

use nexus_prime_core::*;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize the system
    initialize_nexus()?;
    
    // Run the main loop
    run_nexus().await?;
    
    Ok(())
}
