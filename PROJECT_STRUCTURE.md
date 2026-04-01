# ACRCloud CLI Project Structure

```
acrcloud-cli/
├── acrcloud_cli/              # Main package
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Entry point for python -m acrcloud_cli
│   ├── main.py                # CLI main entry point with command groups
│   ├── api.py                 # ACRCloud API client
│   ├── config.py              # Configuration management
│   ├── utils.py               # Utility functions
│   └── commands/              # Command modules
│       ├── __init__.py
│       ├── buckets.py         # Bucket management commands
│       ├── channels.py        # Channel management commands
│       ├── config_cmd.py      # Configuration commands
│       ├── files.py           # File management commands
│       ├── projects.py        # Project management commands
│       ├── filescan.py        # File Scanning commands
│       └── bmprojects.py      # BM Projects commands
├── tests/                     # Test suite
│   ├── __init__.py
│   └── test_config.py         # Configuration tests
├── examples/                  # Usage examples
│   └── basic_usage.sh         # Basic usage examples
├── setup.py                   # Package setup
├── requirements.txt           # Dependencies
├── MANIFEST.in                # Package manifest
├── Makefile                   # Build automation
├── README.md                  # Documentation
├── LICENSE                    # MIT License
└── .gitignore                 # Git ignore rules
```

## Module Descriptions

### Core Modules

- **main.py**: CLI entry point, command group registration, authentication handling
- **api.py**: ACRCloud API client with methods for all API endpoints
- **config.py**: Configuration management (load/save config files)
- **utils.py**: Helper functions for output formatting and validation

### Command Modules

- **buckets.py**: Commands for bucket CRUD operations
- **files.py**: Commands for file upload, download, and management
- **channels.py**: Commands for live channel management
- **projects.py**: Commands for recognition project management
- **config_cmd.py**: Commands for CLI configuration

## API Coverage

### Buckets API
- [x] List buckets
- [x] Get bucket
- [x] Create bucket
- [x] Update bucket
- [x] Delete bucket

### Audio Files API
- [x] List files
- [x] Get file
- [x] Upload file (audio, fingerprint, URL, ACRID)
- [x] Update file
- [x] Delete file
- [x] Batch delete files
- [x] Move files between buckets
- [x] Dump files information

### Live Channels API
- [x] List channels
- [x] Get channel
- [x] Create channel
- [x] Update channel
- [x] Delete channel

### Base Projects API
- [x] List projects
- [x] Get project
- [x] Create project
- [x] Update project
- [x] Delete project
- [x] Get project bucket status
- [x] Get project statistics

### File Scanning API
- [x] List FS containers
- [x] Get FS container
- [x] Create FS container
- [x] Update FS container
- [x] Delete FS container
- [x] List FS files
- [x] Get FS file
- [x] Upload FS file
- [x] Delete FS files
- [x] Rescan FS files

### BM Custom Streams Projects API
- [x] List BM CS projects
- [x] Get BM CS project
- [x] Create BM CS project
- [x] Update BM CS project
- [x] Delete BM CS project
- [x] Set result callback URL
- [x] List BM streams
- [x] Add BM stream
- [x] Update BM stream
- [x] Delete BM streams
- [x] Pause BM streams
- [x] Restart BM streams
