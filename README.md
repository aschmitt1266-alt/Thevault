# The Vault — Android Prototype 0.1

This is the first Android-focused rebuild of the Windows launcher. It is intentionally
kept separate from the working Windows project.

## What this test contains

- Full-screen landscape interface
- The Vault green/yellow theme
- Splash/loading screen
- System-selection screen
- Prototype game lists
- Touch input
- Keyboard/D-pad/controller-style navigation
- Back navigation
- Safe placeholder when a game is selected

This build does **not** launch RetroArch yet. The first test is meant to prove that
the screen sizing and controls work correctly on the phone.

## Run it on a Windows PC first

Install Python 3.10–3.12 and run:

    py -m pip install kivy==2.3.1
    py main.py

## Build the APK with GitHub Actions

1. Create a new private GitHub repository.
2. Upload every file and folder from this project.
3. Open the repository's **Actions** tab.
4. Run **Build Android APK**.
5. When it finishes, download the `the-vault-debug-apk` artifact.
6. Extract the downloaded ZIP and transfer the APK to the Android phone.
7. On the phone, allow installation from the browser or file manager used to open it.
8. Install and open The Vault.

## Build locally using WSL2/Ubuntu

Buildozer's Android toolchain runs on Linux. From Ubuntu/WSL:

    sudo apt update
    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
        python3-venv autoconf libtool pkg-config zlib1g-dev \
        libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install buildozer cython
    buildozer android debug

The resulting APK should appear inside the `bin` folder.

## Phone test checklist

- Does the app remain landscape and fill the screen?
- Is any important text hidden behind the camera cutout?
- Can every system button be touched?
- Does an Xbox controller move the highlight?
- Does A activate the highlighted item?
- Does B return from games to systems?
- Is text comfortably readable from the phone's normal viewing distance?

## Next phase

After the phone interface test passes:

1. Add Android storage-folder selection.
2. Scan real ROM filenames and box art.
3. Detect installed RetroArch/emulator packages.
4. Test launching games through Android intents.
5. Add settings and persistent configuration.
