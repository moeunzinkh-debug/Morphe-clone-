/*
 * Copyright (C) 2026 Morphe.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.microg.gms.ui.updater

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Tests the archive checks the updater runs on a downloaded update package.
 *
 * A download that ends early keeps the local file headers but loses the central
 * directory. The package installer rejects such a file with a misleading "its
 * certificates are missing" error, and the security scanners that look at the same
 * file report the application as malware, so it must never reach the installer.
 */
class ApkArchiveValidationTest {

    private val workDir: File = File(System.getProperty("java.io.tmpdir"), "microg-updater-test")

    @Before
    fun createWorkDir() {
        workDir.mkdirs()
    }

    @Test
    fun aWellFormedArchiveIsAccepted() {
        val apk = writeArchive("good.apk")
        assertNull(AppUpdater.validateApkArchive(apk, apk.length()))
    }

    @Test
    fun aTruncatedArchiveIsRejected() {
        val apk = writeArchive("full.apk")
        val truncated = File(workDir, "full.apk.truncated")
        val data = apk.readBytes()
        truncated.writeBytes(data.copyOf(data.size - 64))
        val problem = AppUpdater.validateApkArchive(truncated, 0)
        assertNotNull("a truncated archive must be rejected", problem)
        assertTrue(problem!!.contains("not a valid APK/ZIP archive"))
    }

    @Test
    fun anEmptyFileIsRejected() {
        val empty = File(workDir, "empty.apk")
        empty.writeBytes(ByteArray(0))
        assertNotNull(AppUpdater.validateApkArchive(empty, 0))
    }

    @Test
    fun aFileThatIsNotAnArchiveIsRejected() {
        val notAnArchive = File(workDir, "garbage.apk")
        notAnArchive.writeBytes("this is not a zip file".toByteArray())
        assertNotNull(AppUpdater.validateApkArchive(notAnArchive, 0))
    }

    @Test
    fun aSizeMismatchIsRejected() {
        val apk = writeArchive("sized.apk")
        val problem = AppUpdater.validateApkArchive(apk, apk.length() + 1)
        assertNotNull("a size mismatch must be rejected", problem)
        assertTrue(problem!!.contains("size mismatch"))
    }

    @Test
    fun anArchiveWithoutAManifestIsRejected() {
        val apk = writeArchive("nomanifest.apk", withManifest = false)
        val problem = AppUpdater.validateApkArchive(apk, 0)
        assertNotNull(problem)
        assertTrue(problem!!.contains("AndroidManifest.xml"))
    }

    @Test
    fun anArchiveWithoutDexCodeIsRejected() {
        val apk = writeArchive("nodex.apk", withDex = false)
        val problem = AppUpdater.validateApkArchive(apk, 0)
        assertNotNull(problem)
        assertTrue(problem!!.contains("dex"))
    }

    /** Writes a small, but structurally valid, APK-like archive. */
    private fun writeArchive(name: String, withManifest: Boolean = true, withDex: Boolean = true): File {
        workDir.mkdirs()
        val file = File(workDir, name)
        ZipOutputStream(FileOutputStream(file)).use { zip ->
            if (withManifest) {
                zip.putNextEntry(ZipEntry("AndroidManifest.xml"))
                zip.write("not-a-real-manifest".toByteArray())
                zip.closeEntry()
            }
            if (withDex) {
                zip.putNextEntry(ZipEntry("classes.dex"))
                zip.write("not-a-real-dex".toByteArray())
                zip.closeEntry()
            }
        }
        return file
    }
}
