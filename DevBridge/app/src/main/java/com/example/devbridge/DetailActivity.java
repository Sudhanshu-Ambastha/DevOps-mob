package com.example.devbridge;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;

public class DetailActivity extends AppCompatActivity {
    private Problem p;
    private TextView solution;
    private MaterialButton vote, comments;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_detail);
        Ui.lightIcons(this);
        Ui.top(findViewById(R.id.dBar));
        Ui.bottom(findViewById(R.id.dScroll));

        p = Repo.I.byId(getIntent().getIntExtra("id", -1));
        if (p == null) { finish(); return; }

        ((TextView) findViewById(R.id.dCat)).setText(p.category.toUpperCase());
        ((TextView) findViewById(R.id.dTitle)).setText(p.title);
        ((TextView) findViewById(R.id.dDesc)).setText(p.desc);
        ((TextView) findViewById(R.id.dMeta)).setText(p.merged + " report(s) merged");
        ((TextView) findViewById(R.id.dSrs)).setText(Repo.I.generateSrs(p));
        solution = findViewById(R.id.dSolution);
        vote = findViewById(R.id.dVote);
        comments = findViewById(R.id.dComments);
        MaterialButton post = findViewById(R.id.dPost);

        refresh();
        findViewById(R.id.dBack).setOnClickListener(x -> finish());

        vote.setOnClickListener(x -> {
            p.voted = !p.voted; p.votes += p.voted ? 1 : -1; refresh();
            vote.animate().scaleX(1.25f).scaleY(1.25f).setDuration(120)
                    .withEndAction(() -> vote.animate().scaleX(1f).scaleY(1f).setDuration(160)).start();
        });

        comments.setOnClickListener(x -> {
            Intent in = new Intent(this, CommentsActivity.class);
            in.putExtra("id", p.id);
            startActivity(in);
        });

        if (!Repo.I.role.equals("Developer")) post.setVisibility(View.GONE);
        post.setOnClickListener(x -> {
            EditText e = new EditText(this);
            e.setHint("Describe your solution / link");
            new AlertDialog.Builder(this).setTitle("Publish solution").setView(e)
                    .setPositiveButton("Publish", (d, w) -> {
                        p.solution = e.getText().toString();
                        Repo.I.addNote("A developer posted a solution for: " + p.title);
                        refresh();
                        Snackbar.make(vote, "Solution published. Upvoters notified.", Snackbar.LENGTH_LONG).show();
                    }).setNegativeButton("Cancel", null).show();
        });

        View root = findViewById(R.id.dRoot);
        root.setAlpha(0f); root.setTranslationY(50f);
        root.animate().alpha(1f).translationY(0f).setDuration(450).start();
    }

    @Override protected void onResume() { super.onResume(); if (p != null) refresh(); }

    private void refresh() {
        vote.setText((p.voted ? "▲ " : "△ ") + p.votes + " upvotes");
        comments.setText("Comments (" + p.comments.size() + ")");
        solution.setText(p.solution == null ? "No developer solution yet." : "Solution: " + p.solution);
    }
}