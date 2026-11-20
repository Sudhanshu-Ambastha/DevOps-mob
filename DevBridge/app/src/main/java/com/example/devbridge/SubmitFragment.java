package com.example.devbridge;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.google.android.material.button.MaterialButton;
import com.google.android.material.card.MaterialCardView;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class SubmitFragment extends Fragment {
    private EditText inTitle, inDesc, inTags;
    private MaterialCardView card;
    private TextView similarText;
    private MaterialButton btnViewPost, btnPostNew;
    private Problem currentMatch;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater i, @Nullable ViewGroup c, @Nullable Bundle b) {
        View v = i.inflate(R.layout.fragment_submit, c, false);
        inTitle = v.findViewById(R.id.inTitle);
        inDesc = v.findViewById(R.id.inDesc);
        inTags = v.findViewById(R.id.inTags);
        card = v.findViewById(R.id.similarCard);
        similarText = v.findViewById(R.id.similarText);
        btnViewPost = v.findViewById(R.id.btnViewPost);
        btnPostNew = v.findViewById(R.id.btnPostNew);

        TextWatcher w = new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b2, int c2) {}
            @Override public void onTextChanged(CharSequence s, int a, int b2, int c2) {}
            @Override public void afterTextChanged(Editable e) { checkSimilar(); }
        };
        inTitle.addTextChangedListener(w);
        inDesc.addTextChangedListener(w);
        inTags.addTextChangedListener(w);

        btnViewPost.setOnClickListener(x -> {
            if (currentMatch != null && getContext() != null) {
                Intent intent = new Intent(getContext(), DetailActivity.class);
                intent.putExtra("id", currentMatch.id);
                startActivity(intent);
            }
        });

        btnPostNew.setOnClickListener(x -> submitProblem(true));

        v.findViewById(R.id.btnSubmit).setOnClickListener(x -> submitProblem(false));
        return v;
    }

    private void submitProblem(boolean forceSeparateContext) {
        String t = inTitle.getText().toString().trim();
        String d = inDesc.getText().toString().trim();
        String tags = normalizeTags(inTags.getText().toString());

        if (t.isEmpty() || d.isEmpty()) {
            Toast.makeText(getContext(), "Fill both fields", Toast.LENGTH_SHORT).show();
            return;
        }

        boolean merged = false;
        if (!forceSeparateContext && currentMatch != null && !hasConflictingTags(tags, currentMatch.tags)) {
            currentMatch.votes++;
            currentMatch.merged++;
            if (!tags.isEmpty()) {
                currentMatch.tags = mergeTagStrings(currentMatch.tags, tags);
            }
            Repo.I.addNote("Your report was merged into: " + currentMatch.title);
            merged = true;
        } else {
            Problem created = new Problem(Repo.I.items.size() + 100, t, d, "General", 1);
            created.tags = tags;
            Repo.I.items.add(created);
            Repo.I.addNote("Problem submitted" + (tags.isEmpty() ? "" : " [" + tags + "]") + ": " + t);
        }

        Toast.makeText(getContext(),
                merged ? "Merged with a similar problem + upvoted" : "Problem submitted",
                Toast.LENGTH_LONG).show();

        currentMatch = null;
        inTitle.setText("");
        inDesc.setText("");
        inTags.setText("");
        card.setVisibility(View.GONE);
        ((MainActivity) requireActivity()).goToFeed();
    }

    private void checkSimilar() {
        String query = (inTitle.getText() + " " + inDesc.getText()).trim();
        String userTags = normalizeTags(inTags.getText().toString());
        Problem s = Repo.I.findSimilar(query);
        currentMatch = s;

        if (s != null) {
            boolean tagConflict = hasConflictingTags(userTags, s.tags);
            btnPostNew.setVisibility(tagConflict || !userTags.isEmpty() ? View.VISIBLE : View.GONE);

            String msg = "Looks similar to: \"" + s.title + "\" (" + s.votes + " upvotes).";
            if (tagConflict) {
                msg += " Different context tags detected — tap \"New context\" to keep it separate.";
            } else {
                msg += " Submitting will upvote it instead of duplicating.";
            }
            similarText.setText(msg);

            if (card.getVisibility() != View.VISIBLE) {
                card.setAlpha(0f);
                card.setTranslationY(30f);
                card.setVisibility(View.VISIBLE);
                card.animate().alpha(1f).translationY(0f).setDuration(350).start();
            }
        } else if (card.getVisibility() == View.VISIBLE) {
            card.animate().alpha(0f).setDuration(200)
                    .withEndAction(() -> card.setVisibility(View.GONE)).start();
        }
    }

    private String normalizeTags(String raw) {
        if (raw == null || raw.trim().isEmpty()) return "";
        String[] parts = raw.toLowerCase().split("[,#\\s]+");
        Set<String> clean = new HashSet<>();
        for (String part : parts) {
            String trimmed = part.trim();
            if (!trimmed.isEmpty()) clean.add(trimmed);
        }
        return String.join(", ", clean);
    }

    private String mergeTagStrings(String existing, String added) {
        Set<String> merged = new HashSet<>();
        if (existing != null && !existing.isEmpty()) {
            merged.addAll(Arrays.asList(existing.split("\\s*,\\s*")));
        }
        if (added != null && !added.isEmpty()) {
            merged.addAll(Arrays.asList(added.split("\\s*,\\s*")));
        }
        return String.join(", ", merged);
    }

    private boolean hasConflictingTags(String userTags, String existingTags) {
        if (userTags == null || userTags.isEmpty() || existingTags == null || existingTags.isEmpty()) {
            return false;
        }
        Set<String> uSet = new HashSet<>(Arrays.asList(userTags.split("\\s*,\\s*")));
        Set<String> eSet = new HashSet<>(Arrays.asList(existingTags.split("\\s*,\\s*")));
        uSet.retainAll(eSet);
        return uSet.isEmpty();
    }
}