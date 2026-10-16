# ទាញយក APK ដែលបាន build ពី GitHub Actions

**Build ចុងក្រោយ៖ ជោគជ័យ ✅** · commit `7c2835d` · branch `arena/5e2b0721-morphe-clone`
· រយៈពេល 11 នាទី 21 វិនាទី · ថ្ងៃទី 16 តុលា 2026

code ដែល build = upstream ដើម 100% (មានតែ docs/tools/CI បន្ថែម ដែលមិនចូល APK)។

---

## 🔗 Link ទាញយក (ត្រូវ login GitHub ដែលជាម្ចាស់ repo)

| ជម្រើស | ទំហំ | សម្រាប់ | Link |
| --- | ---: | --- | --- |
| **arm64-v8a** ⭐ | 42.9 MB | ទូរស័ព្ទទំនើបភាគច្រើន | [ទាញយក](https://github.com/moeunzinkh-debug/Morphe-clone-/actions/runs/38893871605/artifacts/12042939211) |
| armeabi-v7a | 40.7 MB | ទូរស័ព្ទ 32-bit ចាស់ | [ទាញយក](https://github.com/moeunzinkh-debug/Morphe-clone-/actions/runs/38893871605/artifacts/12043013424) |
| universal | 107 MB | មិនដឹង ABI → សុវត្ថិភាពបំផុត | [ទាញយក](https://github.com/moeunzinkh-debug/Morphe-clone-/actions/runs/38893871605/artifacts/12043935294) |

ទំព័រ run ទាំងមូល (មើល job summary, log, ទាញយកឡើងវិញ)៖
<https://github.com/moeunzinkh-debug/Morphe-clone-/actions/runs/38893871605>

Artifact ទាំងនេះ **រក្សាទុក 90 ថ្ងៃ** (ដល់ 14 មករា 2027)។

---

## ✅ ផ្ទៀងផ្ទាត់ឯកសារបន្ទាប់ពីទាញយក

GitHub គណនា SHA-256 ខាងក្រោមនេះ៖

```
microg-arm64-v8a-testsigned.apk      sha256:3e08c83ebc0602c004a3361d9b1030890d2147c90ffdb6854efd9a9d9051d268
microg-armeabi-v7a-testsigned.apk    sha256:e3e8338d2e7845f08026476f7406762303d4ad7e96ae71bfbdb40c61469ad4c7
microg-universal-testsigned.apk      sha256:fc848bdcc92eb1c47c43e472217b4bce0586e90edd8f0cfcaae223c16635ae0e
```

```bash
sha256sum microg-arm64-v8a-testsigned.apk     # Linux/macOS/Termux
certutil -hashfile microg-...apk SHA256       # Windows
```

workflow ខ្លួនឯងក៏បានត្រួតពិនិត្យរួចហើយក្នុង step *"Sign and verify the APK"*៖
`unzip -t` (archive មិនខូច), `apksigner verify --print-certs` (signature អានបាន),
`aapt dump badging` (package/version) — ទាំងអស់ជោគជ័យ។

**ភស្តុតាងថាវាជា build ដូចផ្លូវការ៖**

| | APK ផ្លូវការ 7.2.1 | APK build នេះ | ខុសគ្នា |
| --- | ---: | ---: | ---: |
| arm64-v8a | 44,928,071 B | 44,932,169 B | +4,098 B |
| armeabi-v7a | 42,720,341 B | 42,724,439 B | +4,098 B |
| universal | 112,362,171 B | 112,370,365 B | +8,194 B |

ខុសគ្នាតែប៉ុន្មាន byte — គឺ **signature block** (យើង sign ដោយ key សាកល្បង
មិនមែន key របស់ Morphe)។ ខ្លឹមសារក្នុង APK ដូចគ្នា។

---

## 📲 របៀបដំឡើង

1. **លុប MicroG-RE ចាស់ចេញជាមុន** (ចាំបាច់!) — ព្រោះ APK នេះ sign ដោយ key ផ្សេង។
   បើមិនលុប → "App not installed" / "signature mismatch"។
   ⚠️ ការលុបនឹងបាត់ data/settings របស់ microG (គណនី Google ដែលបានភ្ជាប់… អាចភ្ជាប់ឡើងវិញ)។
2. ទាញយក APK ខាងលើ (ណែនាំ **arm64-v8a**)
3. **Settings → Apps → Special access → Install unknown apps** → អនុញ្ញាតឱ្យ browser/file manager
4. ចុចលើ APK → Install
5. បើកមកជូនដំណឹង "risky app / malware" → ចុច **Ignore** (មិនមែន Fix Now)
   ឬប្រើ ADB៖ `adb install -r -d microg-arm64-v8a-testsigned.apk`
   (មើលឯកសារ `malware-false-positive.md` សម្រាប់វិធីលម្អិត)

---

## 🔁 របៀប build ម្ដងទៀត (ពេលចង់)

- **ស្វ័យប្រវត្តិ**៖ រាល់ push ទៅ `main`, `apk-build` ឬ `arena/**` ដែលប៉ះឯកសារ workflow
  → build ឡើងវិញ
- **ដោយដៃ**៖ បើ workflow នេះមាននៅ `main` ហើយ → **Actions → "Build installable APK" → Run workflow**
  → អាចជ្រើស ABI (all / arm64-v8a / armeabi-v7a / x86_64 / x86)

ឯកសារ workflow៖ [`.github/workflows/build-apk.yml`](../.github/workflows/build-apk.yml)

> ចំណាំ៖ workflow នេះ **មិនកែ code ណាមួយឡើយ** — វាគ្រាន់តែ build,
> sign ដោយ key សាកល្បង, verify និង upload ជា artifact ប៉ុណ្ណោះ។
