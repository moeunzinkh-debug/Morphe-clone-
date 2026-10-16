# ហេតុអ្វី APK របស់យើង ~100MB តែរបស់គេ ~40MB?

**សង្ខេប៖ វាជា build តែមួយបែប ប៉ុន្តែខុសគ្នាត្រង់ចំនួន ABI (ស្ថាបត្យកម្ម CPU)។**

- `microg-<version>.apk` (**universal**) មាន native library ទាំង **4 ABI** (`armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64`) → **~107MB**
- `microg-<version>-icon-arm64-v8a.apk` (**single-ABI**) មានតែ ARM64 → **~43MB** (នេះជារបស់ដែលគេហៅថា "40MB")

កូដ build ដូចគ្នា ប្រភពដូចគ្នា — គ្រាន់តែបញ្ជា build ផ្សេងគ្នា (`-Pabi=...`) ។

## តើ 40MB នោះជា "release APK" មែនទេ?

**បាទ/ចាស — តែ 107MB ក៏ជា release APK ដែរ។** ទាំង 6 asset នៅក្នុង release page
សុទ្ធតែចេញពី task ដូចគ្នា `:play-services-core:assembleDefaultRelease`
(product flavor `default` + build type `release`) រួចចុះហត្ថលេខាដោយ
`ilharp/sign-android-release` ជាមួយ keystore របស់ project (`.github/workflows/release.yml`)។

**ដូច្នេះ ភាពខុសគ្នា 107MB vs 43MB មិនមែន debug vs release ទេ — វាជាចំនួន ABI ។**

| Build type | Command ក្នុង `release.yml` | ABI | Asset | ទំហំ |
| --- | --- | --- | --- | ---: |
| **release** | `assembleDefaultRelease` | 4 | `microg-7.2.1.apk` | 107.16 MB |
| **release** | `assembleDefaultRelease -Pabi=arm64-v8a` | 1 | `...-icon-arm64-v8a.apk` | 42.85 MB |
| **release** | `assembleDefaultRelease -Pabi=armeabi-v7a` | 1 | `...-icon-armeabi-v7a.apk` | 40.74 MB |
| **release** | `assembleDefaultRelease -PnoIcon=true` | 4 | `...-noicon.apk` | 107.16 MB |
| **release** | `assembleDefaultRelease -PnoIcon=true -Pabi=arm64-v8a` | 1 | `...-noicon-arm64-v8a.apk` | 42.85 MB |
| **release** | `assembleDefaultRelease -PnoIcon=true -Pabi=armeabi-v7a` | 1 | `...-noicon-armeabi-v7a.apk` | 40.74 MB |

ចំណាំបន្ថែម៖

- ក្នុង `build.gradle` របស់ `play-services-core` release កំណត់ `minifyEnabled false`
  (គ្មាន R8 shrink) → ដូច្នេះ "release" មិនមានន័យថាតូចទេ។ ទំហំកំណត់ដោយ ABI ។
- Build **debug** ដែលដាក់ `-Pabi` ដូចគ្នា ក៏បានទំហំជិតស្មើគ្នាដែរ (ខុសគ្នាបន្តិចបន្តួច)។
- ពាក្យ `-icon-` / `-noicon-` នៅក្នុងឈ្មោះឯកសារ គ្រាន់តែបង្ហាញ/លាក់ icon ក្នុង launcher
  ប៉ុណ្ណោះ — មិនពាក់ព័ន្ធនឹង build type ឬទំហំទេ។

## លេខពិត (ពី GitHub Release ផ្លូវការ `MorpheApp/MicroG-RE` v7.2.1)

| Asset | ទំហំពិត (bytes) | ទំហំ | ABI នៅក្នុង |
| --- | ---: | ---: | --- |
| `microg-7.2.1.apk` (universal) | 112,362,171 | 107.16 MB | 4 |
| `microg-7.2.1-noicon.apk` (universal) | 112,362,171 | 107.16 MB | 4 |
| `microg-7.2.1-icon-arm64-v8a.apk` | 44,928,071 | 42.85 MB | 1 (arm64) |
| `microg-7.2.1-icon-armeabi-v7a.apk` | 42,720,341 | 40.74 MB | 1 (armv7) |
| `microg-7.2.1-noicon-arm64-v8a.apk` | 44,928,071 | 42.85 MB | 1 (arm64) |
| `microg-7.2.1-noicon-armeabi-v7a.apk` | 42,720,341 | 40.74 MB | 1 (armv7) |

- universal ÷ arm64 = **2.50×**
- 3 ABI បន្ថែម (armv7 + x86 + x86_64) បន្ថែមទម្ងន់ **64.31 MB** បញ្ចូលគ្នាទៅ apex លើ APK universal ។

README ខ្លួនឯងក៏និយាយរួចហើយ៖
> `arm64-v8a` contains only ARM64 native libraries. **The app is less than half the size of the regular release.**

(មិនមែនតែ MicroG-RE ទេ — microG ផ្លូវការ `microg/GmsCore` universal ~103MB, ReVanced `GmsCore` ~100MB។
APK universal របស់ app ប្រភេទ GmsCore គឺ ~100MB ដោយធម្មតា ព្រោះវាមាន map renderer + cronet native ។)

## មូលហេតុច្បាស់លាស់នៅក្នុង code

`play-services-core/build.gradle` (defaultConfig):

```groovy
ndk {
    def requestedAbi = project.findProperty("abi")
    if (!requestedAbi) {
        abiFilters "armeabi-v7a", "arm64-v8a", "x86", "x86_64"   // ← universal: ដាក់ទាំង 4
    }
}
```

និង (splits):

```groovy
splits {
    abi {
        if (project.hasProperty("abi")) {
            enable true
            reset()
            include project.property("abi")   // ← single-ABI: ដាក់តែមួយ
            universalApk false
        } else {
            enable false
        }
    }
}
```

`jniLibs { useLegacyPackaging true }` ធ្វើឱ្យ `.so` ត្រូវបាន **compress** ក្នុង APK ។ ដូច្នេះរាល់ ABI បន្ថែម = ច្បាប់ចម្លង
ថ្មីទាំងស្រុងនៃ library ទាំងអស់ (compress ដែរ) → ទំហំកើនឡើង ~20-25MB ក្នុងមួយ ABI ។

Native library ដែលធ្វើឱ្យ APK ធំ (មកពី AAR dependency ទាំងអស់)៖

| Module | Dependency | ចំណាំ |
| --- | --- | --- |
| `play-services-maps-core-mapbox` | `org.maplibre.gl:android-sdk:10.2.0` (+ turf, annotation) | MapLibre GL — ធំបំផុត |
| `play-services-maps-core-hms` | `com.huawei.hms:maps:6.9.0.300` | HMS maps renderer |
| `play-services-maps-core-vtm` | `org.microg:vtm-android:0.9.1-mod:natives-*` | VTM renderer (shipping 5 ABI) |
| `play-services-cronet-core` | `org.microg:cronet-native:102.5005.125` | Cronet (networking) |

build ទាំង 3 renderer (MapLibre + VTM + HMS) ចូលក្នុង APK តែមួយ ព្រោះ app ជ្រើស renderer
នៅ runtime តាម Settings (មើល comment នៅក្នុង `play-services-core/build.gradle`)។

## វិធី build APK តូច (40MB)

```bash
# ARM64 (ទូរស័ព្ទទំនើបភាគច្រើន) → ~43MB
./gradlew :play-services-core:assembleDefaultRelease -Pabi=arm64-v8a

# ARMv7 32-bit → ~41MB
./gradlew :play-services-core:assembleDefaultRelease -Pabi=armeabi-v7a

# x86_64 (emulator) → តូចជាង
./gradlew :play-services-core:assembleDefaultRelease -Pabi=x86_64
```

Output៖ `play-services-core/build/outputs/apk/default/release/*.apk`
(ឈ្មោះឯកសារបញ្ចប់ដោយ `-arm64-v8a.apk` ។ល។ អាស្រ័យលើ flavor/version ។)

ចង់បាន variant `huawei` ឬ `user` (package `org.microg.gms`)?

```bash
./gradlew :play-services-core:assembleUserRelease -Pabi=arm64-v8a
```

ចង់ឃើញទំហំពិតរបស់ APK ដែលបាន build៖

```bash
python3 tools/apk-size-report.py play-services-core/build/outputs/apk/default/release/*.apk
```

## បើ build តាម GitHub Actions

- Workflow **Release** (`.github/workflows/release.yml`) build ទាំង 6 variants ។
  ក្នុង artifact list សូមជ្រើស `MicroG-RE-arm64-v8a` (42.85MB) ឬ `MicroG-RE-armeabi-v7a` (40.74MB)
  — **មិនមែន** `MicroG-RE` (universal 107.16MB) ទេ។
- Workflow **Gradle build** (`.github/workflows/build.yml`) រត់ `assembleDebug`/`assembleRelease`
  ដោយគ្មាន `-Pabi` → ចេញ APK universal (~107MB) សម្រាប់ផ្ទៀងផ្ទាត់ មិនមែនសម្រាប់ចែកចាយទេ។

## ចំណាំសំខាន់

- **កុំប្រើ `-PnoIcon=true`** ឬ `default` ដោយស្មាន — ជ្រើស ABI ឱ្យត្រូវនឹងឧបករណ៍។
  Universal គឺសុវត្ថិភាពបំផុត តែធំ។
- APK single-ABI **មិនដំណើរការ** លើឧបករណ៍ដែលមាន userspace ខុស (ឧ. armv7 ខណៈឧបករណ៍ត្រូវការ arm64)។
  បើមិនច្បាស់ → ប្រើ universal ។
- app ពិតជាត្រូវដំឡើងលើ `/system` ឬជា privileged app សម្រាប់មុខងារពេញលេញ ដូច្នេះជ្រើស ABI តាមឧបករណ៍
  គឺជាវិធីសុវត្ថិភាពបំផុតក្នុងការកាត់ទំហំ។

## បើចង់តូចជាង 40MB ទៀត

| វិធី | ប៉ាន់ស្មានចំណេញ | ហានិភ័យ |
| --- | --- | --- |
| បំពេញ `minifyEnabled true` + `shrinkResources true` ក្នុង release | ~5–15MB (កាត់ dex + resource ដែលមិនប្រើ) | ត្រូវសាកល្បង — អាចបាក់ reflection/service បើ keep rules មិនគ្រប់ |
| ដក renderer ដែលមិនប្រើ (hms / vtm) ចេញពី `play-services-core/build.gradle` | ច្រើន MB (MapLibre/HMS native) | Settings "Map renderer" នឹងបាត់ជម្រើសនោះ |
| Build AAB រួចប្រើ `bundletool` ចេញ APK តាមឧបករណ៍ | ដូច single-ABI + split resource/density | ត្រូវដំឡើងជា split APK (`install-multiple`) — មិនស្រួលសម្រាប់ sideload |
| ដក `x86`/`x86_64` ចេញពី universal (បើមិនប្រើ emulator) | ~30MB | គ្មានបញ្ហាលើទូរស័ព្ទពិត | 

> សម្គាល់៖ release build បច្ចុប្បន្នកំណត់ `minifyEnabled false` និងមិនមាន `shrinkResources`។
> ការទម្លាក់ទំហំធំៗពិតប្រាកដ (ពី 107MB មក 43MB) មកពីការជ្រើស ABI តែមួយ។
