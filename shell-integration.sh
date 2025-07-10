# OMNIMESH Shell Completion and Aliases
# Add this to your ~/.bashrc or ~/.zshrc

# Aliases for convenience
alias omnimesh='omnimesh'
alias omni='omni'
alias om='omni'  # Even shorter

# Quick shortcuts
alias omni-tui='omni tui'
alias omni-cli='omni cli'
alias omni-c2='omni c2'
alias omni-test='omni test'
alias omni-status='omni status'
alias omni-build='omni build'
alias omni-push='omni push'
alias omni-update='omni update'

# Development shortcuts
alias omni-fe='omni frontend'
alias omni-be='omni backend'
alias omni-logs='omni logs'

# Bash completion for omnimesh commands
_omnimesh_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="launch run tui cli c2 command status test build setup update push help frontend backend logs"
    
    COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
}

# Register completion
complete -F _omnimesh_completion omnimesh
complete -F _omnimesh_completion omni
complete -F _omnimesh_completion om

echo "🌊 OMNIMESH aliases and completion loaded!"
echo "Available commands: omnimesh, omni, om"
echo "Quick shortcuts: omni-tui, omni-cli, omni-c2, omni-test, etc."
