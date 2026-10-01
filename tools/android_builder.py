"""
ساخت پروژه اندروید از صفر + workflow بیلد APK + ریلز
"""

from __future__ import annotations

from typing import Dict


def android_project_files(
    app_name: str,
    package_name: str,
    min_sdk: int = 24,
    target_sdk: int = 34,
) -> Dict[str, str]:
    """برمی‌گرداند path -> content برای یک اپ ساده Kotlin."""

    app_name = (app_name or "MyApp").strip()
    package_name = (package_name or "com.example.myapp").strip()
    pkg_path = package_name.replace(".", "/")

    settings_gradle = f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{app_name}"
include(":app")
"""

    root_build = """plugins {
    id("com.android.application") version "8.2.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
}
"""

    gradle_wrapper_props = """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""

    app_build = f"""plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}}

android {{
    namespace = "{package_name}"
    compileSdk = {target_sdk}

    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = {min_sdk}
        targetSdk = {target_sdk}
        versionCode = 1
        versionName = "1.0.0"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
        debug {{
            applicationIdSuffix = ".debug"
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = "17"
    }}
    buildFeatures {{
        viewBinding = true
    }}
}}

dependencies {{
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
}}
"""

    manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.App">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

    main_activity = f"""package {package_name}

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import {package_name}.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {{
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.titleText.text = getString(R.string.hello_message)
        binding.actionButton.setOnClickListener {{
            binding.titleText.text = getString(R.string.clicked_message)
        }}
    }}
}}
"""

    activity_main = f"""<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="24dp">

    <TextView
        android:id="@+id/titleText"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/hello_message"
        android:textSize="22sp"
        app:layout_constraintBottom_toTopOf="@+id/actionButton"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintVertical_chainStyle="packed" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/actionButton"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="16dp"
        android:text="@string/button_label"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toBottomOf="@+id/titleText" />

</androidx.constraintlayout.widget.ConstraintLayout>
"""

    strings = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{app_name}</string>
    <string name="hello_message">سلام از {app_name}</string>
    <string name="clicked_message">دکمه زده شد ✅</string>
    <string name="button_label">بزن</string>
</resources>
"""

    themes = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.App" parent="Theme.MaterialComponents.DayNight.DarkActionBar">
        <item name="colorPrimary">@color/purple_500</item>
        <item name="colorPrimaryVariant">@color/purple_700</item>
        <item name="colorOnPrimary">@color/white</item>
    </style>
</resources>
"""

    colors = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_500">#6750A4</color>
    <color name="purple_700">#4F378B</color>
    <color name="white">#FFFFFF</color>
</resources>
"""

    proguard = """# Keep default
"""

    # Adaptive icon minimal: use color-only adaptive via xml without png assets
    # Some AGP versions need mipmap - we use adaptive icon referencing color
    ic_launcher_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/purple_500"/>
    <foreground android:drawable="@color/white"/>
</adaptive-icon>
"""

    gitignore = """*.iml
.gradle
/local.properties
/.idea
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
app/build
"""

    readme = f"""# {app_name}

اپ اندروید Kotlin ساخته‌شده توسط GitHub Omni Agent.

## بیلد محلی
```bash
./gradlew assembleRelease
```

## بیلد با GitHub Actions
Workflow `android-build.yml` با هر push به main یا با `workflow_dispatch` یک APK می‌سازد.
با تگ `v*` هم Release + APK منتشر می‌شود.

Package: `{package_name}`
"""

    workflow = f"""name: Android Build & Release

on:
  push:
    branches: [ "main", "master" ]
    tags: [ "v*" ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: "temurin"
          java-version: "17"

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3

      - name: Grant execute permission for gradlew
        run: |
          if [ -f gradlew ]; then chmod +x gradlew; fi

      - name: Build debug APK
        run: |
          if [ -f gradlew ]; then
            ./gradlew assembleDebug --no-daemon
          else
            gradle assembleDebug --no-daemon
          fi

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-debug-apk
          path: app/build/outputs/apk/debug/*.apk

      - name: Build release APK (unsigned)
        run: |
          if [ -f gradlew ]; then
            ./gradlew assembleRelease --no-daemon
          else
            gradle assembleRelease --no-daemon
          fi

      - name: Upload release APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-release-apk
          path: app/build/outputs/apk/release/*.apk

      - name: Publish GitHub Release on tag
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v2
        with:
          files: |
            app/build/outputs/apk/debug/*.apk
            app/build/outputs/apk/release/*.apk
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
"""

    # Note: without gradlew binary we rely on gradle from setup-gradle or install
    # Add a simple gradlew stub instruction - setup-gradle can run gradle

    files = {
        "settings.gradle.kts": settings_gradle,
        "build.gradle.kts": root_build,
        "gradle.properties": "org.gradle.jvmargs=-Xmx2048m\nandroid.useAndroidX=true\nkotlin.code.style=official\n",
        "gradle/wrapper/gradle-wrapper.properties": gradle_wrapper_props,
        "app/build.gradle.kts": app_build,
        "app/proguard-rules.pro": proguard,
        "app/src/main/AndroidManifest.xml": manifest,
        f"app/src/main/java/{pkg_path}/MainActivity.kt": main_activity,
        "app/src/main/res/layout/activity_main.xml": activity_main,
        "app/src/main/res/values/strings.xml": strings,
        "app/src/main/res/values/themes.xml": themes,
        "app/src/main/res/values/colors.xml": colors,
        "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml": ic_launcher_xml,
        "app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml": ic_launcher_xml,
        ".gitignore": gitignore,
        "README.md": readme,
        ".github/workflows/android-build.yml": workflow,
    }
    return files


def scaffold_android_in_repo(gh_tools, owner: str, repo: str, app_name: str, package_name: str, branch: str = "main") -> str:
    files = android_project_files(app_name, package_name)
    results = []
    errors = []
    for path, content in files.items():
        msg = f"Add Android scaffold: {path}"
        out = gh_tools.create_or_update_file(owner, repo, path, content, msg, branch)
        if out.startswith("✅"):
            results.append(path)
        else:
            errors.append(f"{path}: {out}")

    summary = [
        f"### اسکلت اندروید برای `{owner}/{repo}`",
        f"- نام اپ: **{app_name}**",
        f"- پکیج: `{package_name}`",
        f"- فایل‌های موفق: {len(results)}/{len(files)}",
        "",
        "**مرحله بعد:**",
        "1. workflow را با `trigger_workflow` یا push اجرا کن",
        "2. بعد از سبز شدن Actions، APK را از Artifacts دانلود کن",
        "3. برای ریلز عمومی: یک تگ `v1.0.0` بساز تا Release + APK خودکار منتشر شود",
        "",
        "نکته: APK خروجی debug برای تست است؛ release بدون keystore امضای فروشگاهی ندارد.",
    ]
    if errors:
        summary.append("\n### خطاها:")
        summary.extend(f"- {e}" for e in errors[:15])
    return "\n".join(summary)
