#!/usr/bin/env bash
# Build and sign the Watch Face Format APK (resources only, no code).
# Usage: ./build.sh [adb-serial]   (with a serial, also installs)
set -euo pipefail
cd "$(dirname "$0")"

SDK=${ANDROID_HOME:-$HOME/Android/Sdk}
BT=$SDK/build-tools/34.0.0
JAR=$SDK/platforms/android-34/android.jar

uv run -q --with fonttools python -I extras/gen_face.py res/raw/watchface.xml

rm -rf build
mkdir -p build
"$BT/aapt2" compile --dir res -o build/res.zip
"$BT/aapt2" link -I "$JAR" --manifest AndroidManifest.xml \
    --min-sdk-version 34 --target-sdk-version 34 \
    --version-code 1 --version-name 1.0 \
    -o build/unsigned.apk build/res.zip
"$BT/zipalign" -f -p 4 build/unsigned.apk build/aligned.apk
"$BT/apksigner" sign --ks "$HOME/.android/debug.keystore" --ks-pass pass:android \
    --out build/rosepine-watchface.apk build/aligned.apk
echo "built build/rosepine-watchface.apk"

if [[ $# -gt 0 ]]; then
    adb -s "$1" install -r build/rosepine-watchface.apk
fi
