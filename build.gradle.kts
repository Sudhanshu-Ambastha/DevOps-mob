// Root build.gradle.kts
plugins {
    // Leave empty or declare global baseline plugins if needed
}

tasks.register<Delete>("clean") {
    // Clean root build directory
    delete(rootProject.buildDir)
}