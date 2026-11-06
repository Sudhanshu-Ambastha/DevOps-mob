# DevBridge Mobile Client (`mob-dev`)

This directory houses the native Android mobile application for **DevBridge**, built using Java, XML layouts, and ConstraintLayout, integrated seamlessly into the multi-platform repository workspace.

---

## 🏗️ Project Architecture & Setup

The mobile app resides inside the `DevBridge/` subdirectory but is configured via root-level Gradle settings (`settings.gradle`) to allow unified building from the root `DevOps-mob/` workspace while keeping files neatly categorized.

### **Prerequisites**

- **Android Studio:** Ladybug / Jellyfish or newer (supporting Gradle 9.5.0).
- **JDK:** Java 25 (managed automatically via Gradle toolchain support).
- **Gradle Version:** 9.5.0 (`gradle-wrapper.properties`)

---

## 💡 Developer Guide: Viewing All Workspace Files in Android Studio

By default, Android Studio uses the **"Android" view mode** in the left sidebar, which hides non-mobile directories (such as the `ml/` backend core, scripts, and root configuration files) to keep mobile developers focused.

If you need to view, edit, or test backend scripts and mobile code **side-by-side** in the same window:

1. Look at the top-left corner of the left project sidebar (where it currently says **Android** with a dropdown arrow).
2. Click the dropdown menu and change the view mode from **Android** to **Project** or **Project Files**.
3. **Verification:** The sidebar will immediately expand to display the entire `DevOps-mob/` repository tree (`ml/`, `scripts/`, `.github/`, and `DevBridge/`), allowing you to access all project files instantly.

---

## 🚀 Running the App Locally

1. **Open the Workspace:** Open either the root `DevOps-mob/` folder or the inner `DevBridge/` folder directly in Android Studio.
2. **Sync Gradle:** Allow Gradle to sync and download dependencies (Gradle 9.5.0 will be configured automatically).
3. **Run on Emulator:** Select a virtual device (e.g., Pixel 5 / API 26+) from the device dropdown and click the green **Play (Run)** button ▶️.
