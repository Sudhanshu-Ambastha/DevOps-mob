package com.example.devbridge;

import android.app.Activity;
import android.view.View;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;

public class Ui {
    public static void top(View v) { pad(v, true, false); }
    public static void bottom(View v) { pad(v, false, true); }

    private static void pad(View v, boolean top, boolean bottom) {
        final int l = v.getPaddingLeft(), t = v.getPaddingTop(),
                r = v.getPaddingRight(), b = v.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(v, (view, w) -> {
            Insets i = w.getInsets(WindowInsetsCompat.Type.systemBars()
                    | WindowInsetsCompat.Type.displayCutout()
                    | WindowInsetsCompat.Type.ime());
            view.setPadding(l + i.left, t + (top ? i.top : 0), r + i.right, b + (bottom ? i.bottom : 0));
            return w;
        });
    }

    public static void lightIcons(Activity a) {
        WindowCompat.getInsetsController(a.getWindow(), a.getWindow().getDecorView())
                .setAppearanceLightStatusBars(false);
    }
}