# Discord Manual Verification Bot

## Overview

This is a comprehensive Discord bot designed for manual member verification by administrators with automatic role management and moderation features. The bot automatically assigns temporary roles to new members, provides verification commands for administrators, manages role transitions based on gender verification, and includes full moderation capabilities with role preservation. It features comprehensive logging, permission management, and special commands for server entertainment.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Discord.py**: Uses the discord.py library with command extensions for bot functionality
- **Command System**: Implements a prefix-based command system using '+' as the command prefix
- **Intents Configuration**: Enables member and message content intents for full functionality

### Role Management System
- **Temporary Role Assignment**: Automatically assigns temporary roles to new members upon joining
- **Gender-Based Verification**: Provides `+men` and `+wom` commands for administrators to verify members
- **Automatic Role Transition**: Removes temporary roles and assigns permanent gender-specific roles after verification
- **Permission Control**: Restricts verification commands to administrators only

### Moderation System
- **Mute System**: `+mute` command to silence users while preserving their roles
- **Prison System**: `+hebs` command to isolate users in a restricted environment
- **Role Preservation**: Automatically saves user roles before applying sanctions
- **Liberation System**: `+unhebs` command to restore users and their original roles (excluding temporary roles)
- **Dual Command Support**: All commands work via mentions (@user) or message replies

### Entertainment Features
- **Custom Commands**: Special commands like `+omar` that send media content
- **Media Support**: Capability to send videos, images, and other files

### Logging Architecture
- **Dual Logging System**: Implements both file-based logging (bot.log) and console output
- **Discord Logging**: Sends verification actions to a designated Discord log channel
- **Embedded Messages**: Uses Discord embeds for structured log presentation with timestamps

### Configuration Management
- **Environment Variables**: Uses .env file for secure configuration storage
- **Role ID Management**: Stores Discord role IDs for temporary, men's, and women's roles
- **Channel Configuration**: Configurable log channel and guild ID settings

### Event-Driven Architecture
- **Member Join Events**: Automatically triggered when new members join the server
- **Command Events**: Responds to administrator verification commands
- **Asynchronous Processing**: Uses asyncio for non-blocking operations

## External Dependencies

### Core Dependencies
- **discord.py**: Primary Discord API wrapper for bot functionality
- **python-dotenv**: Environment variable management for configuration
- **asyncio**: Asynchronous programming support (built-in Python library)
- **logging**: Comprehensive logging functionality (built-in Python library)
- **datetime**: Timestamp generation for logs (built-in Python library)

### Discord Platform Integration
- **Discord API**: Full integration with Discord's REST API and Gateway
- **Discord Permissions System**: Leverages Discord's role and permission management
- **Discord Embed System**: Uses Discord's rich embed functionality for enhanced log presentation

### Environment Configuration
- **DISCORD_TOKEN**: Bot authentication token
- **Role IDs**: Temporary, men's, and women's role identifiers
- **LOG_CHANNEL_ID**: Designated channel for verification logs
- **GUILD_ID**: Target Discord server identifier