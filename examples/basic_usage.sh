#!/bin/bash
# ACRCloud CLI Basic Usage Examples

# =============================================================================
# Configuration
# =============================================================================

# Set access token
acrcloud config set access_token YOUR_ACCESS_TOKEN

# Verify configuration
acrcloud config list

# =============================================================================
# Bucket Management
# =============================================================================

# List all buckets
acrcloud buckets list

# Create a new bucket for audio files
acrcloud buckets create \
    --name my-music-bucket \
    --type File \
    --region eu-west-1 \
    --labels "Music,Audio"

# Get bucket details (replace 12345 with actual bucket ID)
# acrcloud buckets get 12345

# Update bucket
# acrcloud buckets update 12345 --name new-name --labels "Music,Pop"

# Delete bucket
# acrcloud buckets delete 12345 --yes

# =============================================================================
# File Operations
# =============================================================================

# List files in a bucket (replace 12345 with actual bucket ID)
# acrcloud files list --bucket-id 12345

# Upload an audio file
# acrcloud files upload \
#     --bucket-id 12345 \
#     --file /path/to/audio.mp3 \
#     --title "My Song"

# Upload a fingerprint file
# acrcloud files upload \
#     --bucket-id 12345 \
#     --file /path/to/fingerprint.fp \
#     --type fingerprint \
#     --title "My Fingerprint"

# Upload via URL
# acrcloud files upload \
#     --bucket-id 12345 \
#     --url https://example.com/audio.mp3 \
#     --type audio_url \
#     --title "Remote Audio"

# Get file details
# acrcloud files get 67890 --bucket-id 12345

# Update file
# acrcloud files update 67890 --bucket-id 12345 --title "New Title"

# Delete file
# acrcloud files delete 67890 --bucket-id 12345 --yes

# =============================================================================
# Channel Management
# =============================================================================

# List channels in a bucket
# acrcloud channels list --bucket-id 12345

# Create a live channel
# acrcloud channels create \
#     --bucket-id 12345 \
#     --name "Radio One" \
#     --url "http://stream.example.com/radio" \
#     --record 24 \
#     --timeshift 72

# Get channel details
# acrcloud channels get 67890 --bucket-id 12345

# Update channel
# acrcloud channels update 67890 --bucket-id 12345 --name "New Channel Name"

# Delete channel
# acrcloud channels delete 67890 --bucket-id 12345 --yes

# =============================================================================
# Project Management
# =============================================================================

# List all projects
acrcloud projects list

# Create a new recognition project
acrcloud projects create \
    --name my-recognition-project \
    --type AVR \
    --region eu-west-1 \
    --buckets "12345" \
    --audio-type linein

# Get project details (replace 12345 with actual project ID)
# acrcloud projects get 12345

# Update project
# acrcloud projects update 12345 --name new-project-name

# Get project statistics
# acrcloud projects statistics 12345

# Delete project
# acrcloud projects delete 12345 --yes

# =============================================================================
# Output Formats
# =============================================================================

# JSON output
# acrcloud buckets list --output json
# acrcloud projects list -o json

# Table output (default)
# acrcloud buckets list --output table
# acrcloud files list --bucket-id 12345 -o table
