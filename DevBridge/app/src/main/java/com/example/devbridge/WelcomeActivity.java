package com.example.devbridge;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;

public class WelcomeActivity extends AppCompatActivity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_welcome);
        Ui.lightIcons(this);
        Ui.top(findViewById(R.id.wHero));
        Ui.bottom(findViewById(R.id.wContent));

        int[] ids = {R.id.wTitle, R.id.wSub, R.id.btnUser, R.id.btnDev};
        for (int i = 0; i < ids.length; i++) {
            View v = findViewById(ids[i]);
            v.setAlpha(0f); v.setTranslationY(60f);
            v.animate().alpha(1f).translationY(0f).setStartDelay(i * 150L).setDuration(500).start();
        }
        findViewById(R.id.btnUser).setOnClickListener(x -> go("User"));
        findViewById(R.id.btnDev).setOnClickListener(x -> go("Developer"));
    }

    private void go(String role) {
        Repo.I.role = role;
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }
}