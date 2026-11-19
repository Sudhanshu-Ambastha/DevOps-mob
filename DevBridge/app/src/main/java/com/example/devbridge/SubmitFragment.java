package com.example.devbridge;

import android.os.Bundle;
import android.text.*;
import android.view.*;
import android.widget.*;
import androidx.annotation.*;
import androidx.fragment.app.Fragment;
import com.google.android.material.card.MaterialCardView;

public class SubmitFragment extends Fragment {
    private EditText inTitle, inDesc;
    private MaterialCardView card;
    private TextView similarText;

    @Nullable @Override
    public View onCreateView(@NonNull LayoutInflater i, @Nullable ViewGroup c, @Nullable Bundle b) {
        View v = i.inflate(R.layout.fragment_submit, c, false);
        inTitle = v.findViewById(R.id.inTitle); inDesc = v.findViewById(R.id.inDesc);
        card = v.findViewById(R.id.similarCard); similarText = v.findViewById(R.id.similarText);

        TextWatcher w = new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int b2, int c2) {}
            public void onTextChanged(CharSequence s, int a, int b2, int c2) {}
            public void afterTextChanged(Editable e) { checkSimilar(); }
        };
        inTitle.addTextChangedListener(w); inDesc.addTextChangedListener(w);

        v.findViewById(R.id.btnSubmit).setOnClickListener(x -> {
            String t = inTitle.getText().toString().trim(), d = inDesc.getText().toString().trim();
            if (t.isEmpty() || d.isEmpty()) {
                Toast.makeText(getContext(), "Fill both fields", Toast.LENGTH_SHORT).show();
                return;
            }
            boolean merged = Repo.I.submit(t, d);
            Toast.makeText(getContext(),
                    merged ? "Merged with a similar problem + upvoted" : "Problem submitted",
                    Toast.LENGTH_LONG).show();
            inTitle.setText(""); inDesc.setText("");
            ((MainActivity) requireActivity()).goToFeed();
        });
        return v;
    }

    private void checkSimilar() {
        Problem s = Repo.I.findSimilar(inTitle.getText() + " " + inDesc.getText());
        if (s != null) {
            similarText.setText("Looks similar to: \"" + s.title + "\" (" + s.votes
                    + " upvotes). Submitting will upvote it instead of duplicating.");
            if (card.getVisibility() != View.VISIBLE) {
                card.setAlpha(0f); card.setTranslationY(30f); card.setVisibility(View.VISIBLE);
                card.animate().alpha(1f).translationY(0f).setDuration(350).start();
            }
        } else if (card.getVisibility() == View.VISIBLE) {
            card.animate().alpha(0f).setDuration(200)
                    .withEndAction(() -> card.setVisibility(View.GONE)).start();
        }
    }
}