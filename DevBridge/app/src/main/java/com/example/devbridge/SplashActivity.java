package com.example.devbridge;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.animation.OvershootInterpolator;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;

public class SplashActivity extends AppCompatActivity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_splash);
        Ui.lightIcons(this);

        View logo = findViewById(R.id.logo), tag = findViewById(R.id.tag);
        logo.setScaleX(0.3f); logo.setScaleY(0.3f); logo.setAlpha(0f);
        logo.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(800)
                .setInterpolator(new OvershootInterpolator()).start();
        tag.setAlpha(0f);
        tag.animate().alpha(1f).setStartDelay(600).setDuration(600).start();
        logo.postDelayed(() -> {
            startActivity(new Intent(this, WelcomeActivity.class));
            finish();
        }, 1900);
    }
}