package com.example.devbridge;

import android.os.Bundle;
import android.widget.*;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;

public class CommentsActivity extends AppCompatActivity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_comments);
        Ui.lightIcons(this);
        Ui.top(findViewById(R.id.cBar));
        Ui.bottom(findViewById(R.id.cRoot));

        Problem p = Repo.I.byId(getIntent().getIntExtra("id", -1));
        if (p == null) { finish(); return; }

        ((TextView) findViewById(R.id.cSub)).setText(p.title);
        ListView list = findViewById(R.id.cList);
        EditText input = findViewById(R.id.cInput);
        ArrayAdapter<String> ad = new ArrayAdapter<>(this, R.layout.item_alert, R.id.alertText, p.comments);
        list.setAdapter(ad);
        list.setEmptyView(findViewById(R.id.cEmpty));

        findViewById(R.id.cBack).setOnClickListener(x -> finish());
        findViewById(R.id.cSend).setOnClickListener(x -> {
            String t = input.getText().toString().trim();
            if (t.isEmpty()) return;
            p.comments.add(Repo.I.role + ": " + t);
            Repo.I.addNote("New comment on: " + p.title);
            ad.notifyDataSetChanged();
            list.smoothScrollToPosition(p.comments.size() - 1);
            input.setText("");
        });
    }
}