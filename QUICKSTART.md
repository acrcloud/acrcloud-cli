# ACRCloud CLI Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/acrcloud/acrcloud-cli.git
cd acrcloud-cli

# Install dependencies
pip install -r requirements.txt

# Install the CLI
pip install -e .
```

## Configuration

### 1. Get Your Access Token

1. Log in to [ACRCloud Console](https://console.acrcloud.com)
2. Go to **Account** → **Developer Settings**
3. Create a new access token

### 2. Configure the CLI

```bash
# Set your access token
acrcloud config set access_token YOUR_ACCESS_TOKEN

# Verify configuration
acrcloud config list
```

Or use environment variable:

```bash
export ACRCLOUD_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
```

## Basic Usage

### Buckets

```bash
# List all buckets
acrcloud buckets list

# Create a bucket
acrcloud buckets create --name my-bucket --type File --region eu-west-1

# Get bucket details
acrcloud buckets get 12345

# Update a bucket
acrcloud buckets update 12345 --name new-name

# Delete a bucket
acrcloud buckets delete 12345
```

### Files

```bash
# List files in a bucket
acrcloud buckets files list --bucket-id 12345

# Upload an audio file
acrcloud buckets files upload --bucket-id 12345 --file audio.mp3 --title "My Song"

# Upload a fingerprint
acrcloud buckets files upload --bucket-id 12345 --file fingerprint.fp --type fingerprint

# Upload via URL
acrcloud buckets files upload --bucket-id 12345 --url https://example.com/audio.mp3 --type audio_url

# Delete a file
acrcloud buckets files delete 67890 --bucket-id 12345
```

### Channels

```bash
# List channels
acrcloud buckets channels list --bucket-id 12345

# Create a channel
acrcloud buckets channels create --bucket-id 12345 --name "Radio" --url "http://stream.example.com"

# Delete a channel
acrcloud buckets channels delete 67890 --bucket-id 12345
```

### Projects

```bash
# List projects
acrcloud projects list

# Create a project
acrcloud projects create --name my-project --type AVR --region eu-west-1 --buckets "12345"

# Get project details
acrcloud projects get 12345

# Delete a project
acrcloud projects delete 12345
```

### File Scanning

```bash
# List file scanning containers
acrcloud filescan list-containers

# Create a container
acrcloud filescan create-container --name my-container --region eu-west-1 \
    --buckets "[12345]" --engine 1 --policy-type traverse

# Upload a file for scanning
acrcloud filescan upload --container-id 12345 --region eu-west-1 --file audio.mp3

# List files in container
acrcloud filescan list-files --container-id 12345 --region eu-west-1
```

### BM Projects

```bash
# List BM projects
acrcloud bm-cs-projects list

# Create a BM project
acrcloud bm-cs-projects create --name my-bm --region eu-west-1 --buckets "12345"

# Add a stream
acrcloud bm-cs-projects add-stream 12345 --name "Radio" \
    --url "http://stream.example.com" --config-id 1

# List streams
acrcloud bm-cs-projects list-streams 12345
```

### BM Database Projects

Manage local broadcast database monitoring configurations and query channel metadata via CLI.

```bash
# List DB projects
acrcloud bm-bd-projects list

# List channels in project
acrcloud bm-bd-projects list-channels 12345

# Get non-realtime results for a channel
acrcloud bm-bd-projects channel-results 12345 100251
```

### UCF Projects

Manage User Custom Content (UCF) projects and their detection results.

```bash
# List UCF projects
acrcloud ucf-projects list

# List UCF results for a project
acrcloud ucf-projects list-results 12345

# Get record audio URL for a specific result
acrcloud ucf-projects record-url 12345 340335
```

## Output Formats

```bash
# Table format (default)
acrcloud buckets list

# JSON format
acrcloud buckets list --output json
```

## Help

```bash
# Main help
acrcloud --help

# Command help
acrcloud buckets --help
acrcloud buckets list --help
```
