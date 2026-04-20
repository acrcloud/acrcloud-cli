# ACRCloud CLI

A command-line interface for managing ACRCloud resources via the Console API.

## Features

- **Bucket Management**: Create, list, update, and delete buckets
- **File Operations**: Upload, download, update, and delete audio files and fingerprints
- **Channel Management**: Manage live streaming channels
- **Project Management**: Create and manage recognition projects
- **File Scanning**: Scan audio files for music, cover songs, speech recognition
- **BM Projects**: Broadcast Monitoring custom streams projects and streams
- **Billing & Pricing**: Query bills, invoices, and service pricing
- **Flexible Output**: JSON or table output formats
- **Configuration Management**: Store settings in config files

## Installation

### From Source

```bash
git clone https://github.com/acrcloud/acrcloud-cli.git
cd acrcloud-cli
pip install -e .
```

### Using pip

```bash
pip install acrcloud-cli
```

## Quick Start

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

### 3. Start Using

```bash
# List all buckets
acrcloud buckets list

# Create a new bucket
acrcloud buckets create --name my-bucket --type File --region eu-west-1

# Upload an audio file
acrcloud buckets files upload --bucket-id 12345 --file audio.mp3

# List projects
acrcloud projects list
```

## Commands

### Configuration

```bash
# Set a configuration value
acrcloud config set access_token YOUR_TOKEN
acrcloud config set base_url https://api-v2.acrcloud.com/api

# Get a configuration value
acrcloud config get access_token

# List all configurations
acrcloud config list

# Delete a configuration
acrcloud config delete access_token
```

### Buckets

```bash
# List buckets
acrcloud buckets list
acrcloud buckets list --region eu-west-1 --type File

# Get bucket details
acrcloud buckets get 12345

# Create a bucket
acrcloud buckets create --name my-bucket --type File --region eu-west-1
acrcloud buckets create -n music -t File -r ap-southeast-1 -l "Music,Audio"

# Update a bucket
acrcloud buckets update 12345 --name new-name
acrcloud buckets update 12345 -l "Music,Pop,Rock"

# Delete a bucket
acrcloud buckets delete 12345
acrcloud buckets delete 12345 --yes
```

**Bucket Types:**
- `File`: For audio file recognition
- `Live`: For live stream monitoring
- `LiveRec`: For live stream recording
- `LiveTimeshift`: For timeshift stream monitoring

**Regions:**
- `eu-west-1`: Europe (Ireland)
- `us-west-2`: US West (Oregon)
- `ap-southeast-1`: Asia Pacific (Singapore)

### Files

```bash
# List files in a bucket
acrcloud buckets files list --bucket-id 12345
acrcloud buckets files list -b 12345 --keyword "song"

# Get file details
acrcloud buckets files get 67890 --bucket-id 12345

# Upload audio file
acrcloud buckets files upload --bucket-id 12345 --file audio.mp3
acrcloud buckets files upload -b 12345 -f audio.mp3 --title "My Song"

# Upload fingerprint
acrcloud buckets files upload -b 12345 -f fingerprint.fp -t fingerprint

# Upload via URL
acrcloud buckets files upload -b 12345 -u https://example.com/audio.mp3 -t audio_url

# Upload by ACRID
acrcloud buckets files upload -b 12345 -a "ACRID123" -t acrid

# Update file
acrcloud buckets files update 67890 --bucket-id 12345 --title "New Title"

# Delete file
acrcloud buckets files delete 67890 --bucket-id 12345

# Delete multiple files
acrcloud buckets files delete-batch --bucket-id 12345 --file-ids "1,2,3"

# Move files to another bucket
acrcloud buckets files move --bucket-id 12345 --target-bucket-id 67890 --file-ids "1,2,3"

# Dump all files (once per day)
acrcloud buckets files dump --bucket-id 12345
```

### Channels

```bash
# List channels
acrcloud buckets channels list --bucket-id 12345

# Get channel details
acrcloud buckets channels get 67890 --bucket-id 12345

# Create channel
acrcloud buckets channels create --bucket-id 12345 --name "Radio One" --url "http://stream.example.com/radio"
acrcloud buckets channels create -b 12345 -n "TV Channel" -u "http://tv.example.com/stream" -r 24 -t 72

# Update channel
acrcloud buckets channels update 67890 --bucket-id 12345 --name "New Name"

# Delete channel
acrcloud buckets channels delete 67890 --bucket-id 12345
```

### Projects

```bash
# List projects
acrcloud projects list

# Get project details
acrcloud projects get 12345

# Create project
acrcloud projects create --name my-project --type AVR --region eu-west-1 --buckets "1,2,3"
acrcloud projects create -n music-detection -t AVR -r ap-southeast-1 -b "12345"

# Update project
acrcloud projects update 12345 --name new-name
acrcloud projects update 12345 -b "1,2,3,4"

# Delete project
acrcloud projects delete 12345

# Get bucket status
acrcloud projects bucket-status 12345

# Get statistics
acrcloud projects statistics 12345
acrcloud projects statistics 12345 --start-date 2024-01-01 --end-date 2024-12-31
```

**Project Types:**
- `AVR`: Audio/Video Recognition - for detecting music or custom content
- `LCD`: Live Channel Detection - for detecting live channels and time-shifting channels
- `HR`: Hybrid Recognition - for detecting both live channels and custom content

### File Scanning

```bash
# List file scanning containers
acrcloud filescan list-containers
acrcloud filescan list-containers --region eu-west-1

# Get container details
acrcloud filescan get-container 12345

# Create a container
acrcloud filescan create-container --name my-container --region eu-west-1 \\
    --buckets "[12345,67890]" --engine 1 --policy-type traverse

# Update a container
acrcloud filescan update-container 12345 --name new-name

# Delete a container
acrcloud filescan delete-container 12345

# List files in a container (region is optional, auto-resolved from container)
acrcloud filescan list-files --container-id 12345
acrcloud filescan list-files --container-id 12345 --region eu-west-1

# Upload a file for scanning (region and type are optional, auto-detected)
acrcloud filescan upload --container-id 12345 --file audio.mp3
acrcloud filescan upload -c 12345 -u https://example.com/audio.mp3 -t audio_url
acrcloud filescan upload -c 12345 -f fingerprint.fp -t fingerprint

# Get file results (region is optional, auto-resolved from container)
acrcloud filescan get-file FILE_ID --container-id 12345
acrcloud filescan get-file FILE_ID --container-id 12345 --region eu-west-1

# Delete files (region is optional)
acrcloud filescan delete-files --container-id 12345 --file-ids "id1,id2"

# Rescan files (region is optional)
acrcloud filescan rescan --container-id 12345 --file-ids "id1,id2"

# Scan a file (auto-detects container, creates one if needed, polls for results)
acrcloud filescan scan audio.mp3
acrcloud filescan scan audio.mp3 --container-id 12345
acrcloud filescan scan audio.mp3 --region eu-west-1 --engine 1 --buckets "23,24"
acrcloud filescan scan fingerprint.fp --container-id 12345
acrcloud filescan scan audio.mp3 --poll-interval 5 --timeout 600
acrcloud filescan scan audio.mp3 --poll-interval 5 --timeout 600
```

**Engines:**
- `1`: Audio Fingerprinting
- `2`: Cover Songs
- `3`: Audio Fingerprinting & Cover songs
- `4`: Speech to Text

**Notes:**
- `--region` is optional for all file operations. If not provided, the container's region is automatically resolved from the main API.
- `--type` is optional for upload. The CLI auto-detects the type based on file extension and content (`.fp` files are detected as `fingerprint`, common audio formats as `audio`).
- Container info is cached locally (~/.acrcloud/container_cache.json) for 30 minutes to reduce API calls.
- The `scan` command auto-detects data type, searches for matching containers, uploads the file, and polls for results (default poll interval: 5s, timeout: 600s).

### BM Projects (Broadcast Monitoring)

```bash
# List BM custom streams projects
acrcloud bm-cs-projects list
acrcloud bm-cs-projects list --region eu-west-1

# Get project details
acrcloud bm-cs-projects get 12345

# Create a BM project
acrcloud bm-cs-projects create --name my-bm-project --region eu-west-1 --buckets "12345,67890"

# Update a BM project
acrcloud bm-cs-projects update 12345 --name new-name

# Delete a BM project
acrcloud bm-cs-projects delete 12345

# Set result callback URL
acrcloud bm-cs-projects set-callback 12345 --url https://callback.example.com/results

# List streams in a project
acrcloud bm-cs-projects list-streams 12345
acrcloud bm-cs-projects list-streams 12345 --state Running

# Add a stream
acrcloud bm-cs-projects add-stream 12345 --name "Radio One" \\
    --url "http://stream.example.com" --config-id 1

# Update a stream
acrcloud bm-cs-projects update-stream 12345 s-ABC123 --name "New Name"

# Delete streams
acrcloud bm-cs-projects delete-streams 12345 --stream-ids "s-ABC123,s-DEF456"

# Pause streams
acrcloud bm-cs-projects pause-streams 12345 --stream-ids "s-ABC123,s-DEF456"

# Restart streams
acrcloud bm-cs-projects restart-streams 12345 --stream-ids "s-ABC123,s-DEF456"

# Stream state
acrcloud bm-cs-projects stream-state 12345 s-ABC123

# Stream results
acrcloud bm-cs-projects stream-results 12345 s-ABC123 --date 20210201

# Analytics
acrcloud bm-cs-projects analytics 12345 --stats-type date --result-type music

# Stream recording
acrcloud bm-cs-projects stream-recording 12345 s-ABC123 -t 20210607000210 -d 30
```

**Project Types:**
- `BM-ACRC`: Server-side audio ingestion
- `BM-LOCAL`: Local monitoring tool audio ingestion

### BM Database Projects

Manage Broadcast Monitoring Database projects, channels, results, user reports, and analytics.

```bash
# List BM database projects
acrcloud bm-db-projects list
acrcloud bm-db-projects list -r eu-west-1

# Create a project
acrcloud bm-db-projects create --name my-db-project --region eu-west-1 --buckets "14661"

# Add channels
acrcloud bm-db-projects add-channels 12345 --channels "238766"

# List channels
acrcloud bm-db-projects list-channels 12345

# Channel results
acrcloud bm-db-projects channel-results 12345 238766 -d 20210201

# Real-time results
acrcloud bm-db-projects realtime-results 12345 238766
```

### UCF Projects

Manage User Custom Content (UCF) projects, importing BM streams, and querying results.

```bash
# List UCF projects
acrcloud ucf-projects list

# Create a project
acrcloud ucf-projects create --name my-ucf-project --region eu-west-1 --type BM

# Import BM streams
acrcloud ucf-projects import-streams 12345 --bm-stream-ids "191149,198144" --origin-from BM-DATABASE --bm-project-id 871

# List streams
acrcloud ucf-projects list-streams 12345

# List results
acrcloud ucf-projects list-results 12345

# Get UCF record URL
acrcloud ucf-projects record-url 12345 340335
```

### Billing & Pricing

Query your billing information, invoices, and service pricing.

```bash
# Get current bill
acrcloud billing current-bill
acrcloud billing current-bill --output json

# Get next bill date
acrcloud billing next-bill-date

# List invoices
acrcloud billing invoices
acrcloud billing invoices --per-page 50

# Download invoice PDF
acrcloud billing download-invoice 12345-67890
acrcloud billing download-invoice 12345-67890 --output-file ~/my_invoice.pdf

# Get pricing information
acrcloud billing prices
acrcloud billing prices --type Standard
acrcloud billing prices --service-types AVR,LCD,BM

```

**Price Types:**
- `Latest` (default): Latest prices grouped by service type
- `Standard`: Default prices (uid=0)
- `All`: All prices for uid 0 and the specified uid

**Service Types:** `AVR`, `LCD`, `BM`, `HR`, etc.

## Global Options

```bash
# Use custom config file
acrcloud --config /path/to/config.json buckets list

# Specify access token directly
acrcloud --access-token YOUR_TOKEN buckets list

# Enable verbose output
acrcloud -v buckets list

# Show version
acrcloud --version

# Show help
acrcloud --help
acrcloud buckets --help
acrcloud buckets list --help
```

## Output Formats

```bash
# Table format (default)
acrcloud buckets list

# JSON format
acrcloud buckets list --output json
acrcloud buckets get 12345 -o json
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ACRCLOUD_ACCESS_TOKEN` | Your ACRCloud access token |

## Configuration File

Default location: `~/.acrcloud/config.json`

Example:

```json
{
  "access_token": "your_access_token_here",
  "base_url": "https://api-v2.acrcloud.com/api"
}
```

## API Documentation

For more details about the API, visit:
- [Console API Documentation](https://docs.acrcloud.com/reference/console-api)
- [Identification API](https://docs.acrcloud.com/reference/identification-api)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please contact:
- Email: support@acrcloud.com
- Website: https://www.acrcloud.com
