# tims-bot README

# Tims Bot

Tims Bot is a Telegram bot that allows users to search for music on YouTube and download audio files. It utilizes the `yt-dlp` library for downloading and `ffmpeg` for audio processing.

## Project Structure

```
tims-bot
├── src
│   └── main.py          # Main logic for the Telegram bot
├── downloads            # Directory for storing downloaded audio files
├── requirements.txt     # Python dependencies
├── render.yaml          # Configuration for deploying on Render.com
└── README.md            # Project documentation
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd tims-bot
   ```

2. **Install dependencies**:
   Make sure you have Python installed, then run:
   ```
   pip install -r requirements.txt
   ```

3. **FFmpeg Installation**:
   Ensure that FFmpeg is installed on your system. You can download it from [FFmpeg's official website](https://ffmpeg.org/download.html). 

4. **Set Environment Variables**:
   You need to set the `FFMPEG_PATH` environment variable to the path where FFmpeg is installed. This can be done in your system settings or in the Render.com dashboard.

## Usage

1. **Run the bot**:
   Execute the following command to start the bot:
   ```
   python src/main.py
   ```

2. **Interact with the bot**:
   - Send a song name to the bot, and it will return the top 10 YouTube results.
   - Choose a song to download, and the bot will send you the audio file.

## Deployment on Render.com

To deploy this project on Render.com, follow these steps:

1. Create a new web service on Render.com.
2. Connect your GitHub repository containing the project.
3. In the Render dashboard, specify the build command as:
   ```
   pip install -r requirements.txt
   ```
4. Set the environment variable for FFmpeg:
   - Key: `FFMPEG_PATH`
   - Value: Path to your FFmpeg installation.
5. Set the start command to:
   ```
   python src/main.py
   ```
6. Deploy the service.

Make sure to check the Render documentation for any additional configurations specific to your setup.