import boto3, subprocess, tempfile, os, re, json, time

def merge_videos_with_mediaconvert(s3_urls, output_bucket, output_key_prefix, role_arn, region="us-east-1"):
    """
    Merge multiple public S3 MP4 videos into one using AWS MediaConvert,
    preserving different audio tracks.

    Args:
        s3_urls (list[str]): List of public S3 URLs.
        output_bucket (str): Output S3 bucket name.
        output_key_prefix (str): Output folder/prefix.
        role_arn (str): IAM Role ARN for MediaConvert to write output.
        region (str): AWS region.

    Returns:
        str: Public S3 URL of the merged video.
    """

    # Convert https URLs to s3:// format
    def url_to_s3_path(url):
        match = re.match(r"https://([^/]+)\.s3\.amazonaws\.com/(.+)", url)
        if not match:
            raise ValueError(f"Invalid S3 URL: {url}")
        bucket, key = match.groups()
        return f"s3://{bucket}/{key}"


    output_filename = f"merged_{int(time.time())}"
    destination_s3 = f"s3://{output_bucket}/{output_key_prefix}/{output_filename}"

    mc_client = boto3.client("mediaconvert", region_name=region)
    endpoint = mc_client.describe_endpoints()["Endpoints"][0]["Url"]
    mc_client = boto3.client("mediaconvert", endpoint_url=endpoint, region_name=region)


    inputs = []
    audio_descriptions = []

    for i, url in enumerate(s3_urls):
        selector_name = f"AudioSelector{i}"
        inputs.append({
            "FileInput": url_to_s3_path(url),
            "TimecodeSource": "ZEROBASED",
            "AudioSelectors": {
                selector_name: {"DefaultSelection": "DEFAULT"}
            }
        })
        audio_descriptions.append({
            "AudioSourceName": selector_name,
            "CodecSettings": {
                "Codec": "AAC",
                "AacSettings": {
                    "Bitrate": 96000,
                    "CodingMode": "CODING_MODE_2_0",
                    "SampleRate": 48000
                }
            }
        })

    # Job settings
    job_settings = {
        "Inputs": inputs,
        "OutputGroups": [
            {
                "Name": "File Group",
                "OutputGroupSettings": {
                    "Type": "FILE_GROUP_SETTINGS",
                    "FileGroupSettings": {"Destination": destination_s3}
                },
                "Outputs": [
                    {
                        "ContainerSettings": {"Container": "MP4"},
                        "VideoDescription": {
                            "CodecSettings": {
                                "Codec": "H_264",
                                "H264Settings": {
                                    "RateControlMode": "QVBR",
                                    "MaxBitrate": 5000000,
                                    "QualityTuningLevel": "SINGLE_PASS"
                                }
                            }
                        },
                        #"AudioDescriptions": audio_descriptions
                    }
                ]
            }
        ]
    }

    # Create MediaConvert job
    job = mc_client.create_job(Role=role_arn, Settings=job_settings)
    job_id = job["Job"]["Id"]
    print(f"MediaConvert job started with Job ID: {job_id}")


    while True:
        job_status = mc_client.get_job(Id=job_id)["Job"]["Status"]
        print(f"Job status: {job_status}")

        if job_status in ("COMPLETE", "ERROR", "CANCELED"):
            break
        time.sleep(10)

    if job_status != "COMPLETE":
        job_detail = mc_client.get_job(Id=job_id)["Job"]
        error_message = job_detail.get("ErrorMessage", "No detailed error message available")
        raise RuntimeError(f"MediaConvert job failed with status {job_status}: {error_message}")

    # Return public URL
    output_url = f"https://{output_bucket}.s3.amazonaws.com/{output_key_prefix}/{output_filename}.mp4"
    print(f"Merged video available at: {output_url}")

    return output_url



def get_duration(path, ffprobe_path: str=''):
    """Return clip duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            ffprobe_path, "-v", "error", "-show_entries",
            "format=duration", "-of", "json", path
        ],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

def download_s3_url(url, tmpdir, s3):
        match = re.match(r"https://([^/]+)\.s3\.amazonaws\.com/(.+)", url)
        if not match:
            raise ValueError(f"Invalid S3 URL: {url}")
        bucket, key = match.groups()
        local_path = os.path.join(tmpdir, os.path.basename(key))
        s3.download_file(bucket, key, local_path)
        return local_path

def merge_s3_videos_crossfade_noaudio(
        s3_urls, fade_duration=1.0, ffmpeg_path: str='', ffprobe_path: str=''
    ):
    """
    Merge S3 MP4 videos (no audio) with smooth crossfades.
    Keeps correct overall length by calculating accurate offsets.
    Returns: merged video bytes (MP4)
    """
    if len(s3_urls) < 2:
        raise ValueError("Need at least two S3 videos to merge.")

    s3 = boto3.client("s3")

    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        local_files = [download_s3_url(u, tmpdir, s3) for u in s3_urls]
        durations = [get_duration(f, ffprobe_path) for f in local_files]
        n = len(local_files)

        output_path = os.path.join(tmpdir, "merged_crossfade.mp4")
        input_args = " ".join(f"-i {f}" for f in local_files)

        # cumulative offset logic
        offsets = []
        current_time = 0.0
        for i in range(n - 1):
            offset = current_time + (durations[i] - fade_duration)
            offsets.append(offset)
            current_time = offset
        # build filter chain
        filter_parts = []
        for i, offset in enumerate(offsets):
            v_in = f"[v{i}]" if i > 0 else f"[{i}:v]"
            filter_parts.append(
                f"{v_in}[{i+1}:v]xfade=transition=fadeblack:"
                f"duration={fade_duration}:offset={offset}[v{i+1}];"
            )

        filter_chain = "".join(filter_parts)
        last_v = f"v{n-1}"

        cmd = (
            f"{ffmpeg_path} -y {input_args} "
            f"-filter_complex \"{filter_chain[:-1]}\" "
            f"-map \"[{last_v}]\" -an "
            f"-c:v libx264 -crf 20 -preset medium -movflags +faststart {output_path}"
        )

        print("Running FFmpeg merge with true offsets...")
        subprocess.run(cmd, shell=True, check=True)

        with open(output_path, "rb") as f:
            return f.read()



# s3_urls = [
#     "https://experiment-gaana.s3.amazonaws.com/assets/videos/37656c8e-c4b5-4eec-a64b-34cf2d4c3807/chunks/0_1762365971.mp4",
#     "https://experiment-gaana.s3.amazonaws.com/assets/videos/37656c8e-c4b5-4eec-a64b-34cf2d4c3807/chunks/1_1762366033.mp4",
#     "https://experiment-gaana.s3.amazonaws.com/assets/videos/37656c8e-c4b5-4eec-a64b-34cf2d4c3807/chunks/2_1762366105.mp4"
# ]

# merged_url = merge_videos_with_mediaconvert(
#     s3_urls,
#     output_bucket="staging-gaana",
#     output_key_prefix="assets/videos/merged",
#     role_arn="arn:aws:iam::506569801059:role/media-convert"
# )

# print("Merged video URL:", merged_url)


# video_bytes = merge_s3_videos_crossfade_noaudio(s3_urls, fade_duration=1)

# # Save locally for viewing
# with open("merged_smooth_noaudio.mp4", "wb") as f:
#     f.write(video_bytes)

# print("✅ Smooth merged video saved: merged_smooth_noaudio.mp4")
