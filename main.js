// API Configuration - Auto-detect base URL
const API_BASE = (() => {
    // In production, use the same origin (current website)
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return `${window.location.origin}/api`;
    }
    // For local development
    return 'http://localhost:5000/api';
})();

// DOM Elements
const urlForm = document.getElementById('urlForm');
const urlInput = document.getElementById('urlInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const videoInfoCard = document.getElementById('videoInfoCard');
const optionsCard = document.getElementById('optionsCard');
const downloadBtn = document.getElementById('downloadBtn');
const progressCard = document.getElementById('progressCard');
const closeProgressBtn = document.getElementById('closeProgressBtn');
const alert = document.getElementById('alert');

// State
let currentVideoInfo = null;
let currentDownloadId = null;
let progressInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    urlForm.addEventListener('submit', handleUrlSubmit);
    
    // Radio buttons for download type
    document.querySelectorAll('input[name="downloadType"]').forEach(radio => {
        radio.addEventListener('change', handleDownloadTypeChange);
    });
    
    downloadBtn.addEventListener('click', handleDownload);
    closeProgressBtn.addEventListener('click', closeProgress);
}

async function handleUrlSubmit(e) {
    e.preventDefault();
    
    const url = urlInput.value.trim();
    if (!url) {
        showAlert('Please enter a valid URL', 'error');
        return;
    }
    
    // Validate URL
    if (!isValidYouTubeUrl(url)) {
        showAlert('Please enter a valid YouTube or YouTube Music URL', 'error');
        return;
    }
    
    analyzeBtn.disabled = true;
    analyzeBtn.classList.add('loading');
    analyzeBtn.querySelector('span').textContent = 'Analyzing...';
    
    try {
        // Get download type (default to video)
        const audioOnly = document.querySelector('input[name="downloadType"]:checked').value === 'audio';
        
        const response = await fetch(`${API_BASE}/video-info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                audio_only: audioOnly
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentVideoInfo = data;
            displayVideoInfo(data);
            populateQualityOptions(data.qualities);
            showOptions();
        } else {
            showAlert(data.error || 'Failed to fetch video information', 'error');
        }
    } catch (error) {
        showAlert('Error connecting to server. Make sure the backend is running.', 'error');
        console.error('Error:', error);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.classList.remove('loading');
        analyzeBtn.querySelector('span').textContent = 'Analyze';
    }
}

function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)\/.+/;
    return youtubeRegex.test(url);
}

function displayVideoInfo(data) {
    // Set thumbnail
    const thumbnail = document.getElementById('videoThumbnail');
    if (data.thumbnail) {
        thumbnail.src = data.thumbnail;
        thumbnail.style.display = 'block';
    } else {
        thumbnail.style.display = 'none';
    }
    
    // Set title
    document.getElementById('videoTitle').textContent = data.title;
    
    // Set duration
    document.getElementById('videoDuration').textContent = `⏱️ ${data.duration}`;
    
    // Set type badge
    const typeBadge = document.getElementById('videoType');
    if (data.is_playlist) {
        typeBadge.textContent = '📋 Playlist';
    } else {
        typeBadge.textContent = '🎥 Video';
    }
    
    // Show/hide zip option
    const zipOptionGroup = document.getElementById('zipOptionGroup');
    if (data.is_playlist) {
        zipOptionGroup.style.display = 'block';
    } else {
        zipOptionGroup.style.display = 'none';
    }
    
    videoInfoCard.style.display = 'block';
}

function populateQualityOptions(qualities) {
    const qualitySelect = document.getElementById('qualitySelect');
    
    // Clear existing options except "Auto"
    qualitySelect.innerHTML = '<option value="auto">Auto (Best Available)</option>';
    
    // Add quality options
    qualities.forEach((quality, index) => {
        const option = document.createElement('option');
        option.value = index + 1;
        option.textContent = `${quality.label} - ${quality.size} (${quality.ext})`;
        qualitySelect.appendChild(option);
    });
}

function showOptions() {
    optionsCard.style.display = 'block';
    optionsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleDownloadTypeChange() {
    // When download type changes, re-analyze the URL
    if (currentVideoInfo) {
        const audioOnly = document.querySelector('input[name="downloadType"]:checked').value === 'audio';
        
        // Re-fetch video info with new audio_only setting
        fetch(`${API_BASE}/video-info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: urlInput.value.trim(),
                audio_only: audioOnly
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentVideoInfo = data;
                populateQualityOptions(data.qualities);
            }
        })
        .catch(err => {
            console.error('Error:', err);
        });
    }
}

async function handleDownload() {
    if (!currentVideoInfo) {
        showAlert('Please analyze a video first', 'warning');
        return;
    }
    
    const url = urlInput.value.trim();
    const audioOnly = document.querySelector('input[name="downloadType"]:checked').value === 'audio';
    const qualityIndex = document.getElementById('qualitySelect').value;
    const createZip = document.getElementById('createZip').checked && currentVideoInfo.is_playlist;
    
    downloadBtn.disabled = true;
    downloadBtn.classList.add('loading');
    
    try {
        const response = await fetch(`${API_BASE}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                format_id: qualityIndex,
                audio_only: audioOnly,
                create_zip: createZip
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentDownloadId = data.download_id;
            showProgress();
            startProgressPolling(data.download_id);
            showAlert('Download started successfully!', 'success');
        } else {
            showAlert(data.error || 'Failed to start download', 'error');
        }
    } catch (error) {
        showAlert('Error connecting to server', 'error');
        console.error('Error:', error);
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.classList.remove('loading');
    }
}

function showProgress() {
    progressCard.style.display = 'block';
    progressCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    updateProgress(0, 'Starting download...');
}

function closeProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    progressCard.style.display = 'none';
    currentDownloadId = null;
}

function startProgressPolling(downloadId) {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/download-status/${downloadId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                updateProgress(100, data.message || 'Download completed!');
                clearInterval(progressInterval);
                progressInterval = null;
                showAlert('Download completed successfully!', 'success');
                
                // Trigger browser download
                if (data.download_file && data.download_filename) {
                    const downloadUrl = `${API_BASE}/download-file?file=${encodeURIComponent(data.download_file)}`;
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.download = data.download_filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    showAlert(`Downloading ${data.download_filename} to your browser...`, 'success');
                }
                
                // Auto-close progress after 5 seconds
                setTimeout(() => {
                    closeProgress();
                }, 5000);
            } else if (data.status === 'error') {
                updateProgress(0, `Error: ${data.error || 'Unknown error'}`);
                clearInterval(progressInterval);
                progressInterval = null;
                showAlert(data.error || 'Download failed', 'error');
            } else if (data.status === 'downloading') {
                updateProgress(data.progress || 0, data.message || 'Downloading...');
            }
        } catch (error) {
            console.error('Error polling progress:', error);
        }
    }, 1000); // Poll every second
}

function updateProgress(percentage, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressMessage = document.getElementById('progressMessage');
    
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = `${Math.round(percentage)}%`;
    progressMessage.textContent = message;
}

function showAlert(message, type = 'success') {
    alert.textContent = message;
    alert.className = `alert ${type}`;
    alert.classList.add('show');
    
    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

