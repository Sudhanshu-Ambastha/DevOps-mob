package com.example.devbridge;

import android.os.Bundle;
import android.view.View;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.fragment.app.Fragment;
import com.google.android.material.bottomnavigation.BottomNavigationView;

public class MainActivity extends AppCompatActivity {
    private BottomNavigationView nav;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        Ui.lightIcons(this);

        nav = findViewById(R.id.nav);
        View header = findViewById(R.id.header);
        Ui.top(header);

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.mRoot), (v, w) -> {
            boolean kb = w.isVisible(WindowInsetsCompat.Type.ime());
            int imeH = w.getInsets(WindowInsetsCompat.Type.ime()).bottom;
            v.setPadding(0, 0, 0, kb ? imeH : 0);
            nav.setVisibility(kb ? View.GONE : View.VISIBLE);
            return w;
        });

        header.setAlpha(0f); header.setTranslationY(-40f);
        header.animate().alpha(1f).translationY(0f).setDuration(600).start();

        nav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_feed) show(new FeedFragment());
            else if (id == R.id.nav_submit) show(new SubmitFragment());
            else if (id == R.id.nav_alerts) show(new AlertsFragment());
            else show(new ProfileFragment());
            return true;
        });
        if (b == null) show(new FeedFragment());
    }

    private void show(Fragment f) {
        getSupportFragmentManager().beginTransaction()
                .setCustomAnimations(android.R.animator.fade_in, android.R.animator.fade_out)
                .replace(R.id.container, f).commit();
    }

    public void goToFeed() { nav.setSelectedItemId(R.id.nav_feed); }
}