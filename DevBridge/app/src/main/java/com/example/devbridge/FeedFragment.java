package com.example.devbridge;

import android.content.Intent;
import android.os.Bundle;
import android.view.*;
import android.view.animation.AnimationUtils;
import android.widget.TextView;
import androidx.annotation.*;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.*;
import com.google.android.material.button.MaterialButton;
import java.util.*;

public class FeedFragment extends Fragment {
    private RecyclerView rv;
    private final List<Problem> data = new ArrayList<>();
    private Adapter ad;

    @Nullable @Override
    public View onCreateView(@NonNull LayoutInflater i, @Nullable ViewGroup c, @Nullable Bundle b) {
        View v = i.inflate(R.layout.fragment_feed, c, false);
        rv = v.findViewById(R.id.rv);
        rv.setLayoutManager(new LinearLayoutManager(getContext()));
        rv.setLayoutAnimation(AnimationUtils.loadLayoutAnimation(getContext(), R.anim.layout_fall));
        ad = new Adapter();
        rv.setAdapter(ad);
        return v;
    }

    @Override public void onResume() {
        super.onResume();
        data.clear(); data.addAll(Repo.I.items);
        Collections.sort(data, (a, b2) -> b2.votes - a.votes);   // most demanded first
        ad.notifyDataSetChanged();
        rv.scheduleLayoutAnimation();
    }

    class Adapter extends RecyclerView.Adapter<Adapter.H> {
        class H extends RecyclerView.ViewHolder {
            TextView cat, title, desc, meta; MaterialButton vote;
            H(View v) {
                super(v);
                cat = v.findViewById(R.id.cat); title = v.findViewById(R.id.title);
                desc = v.findViewById(R.id.desc); meta = v.findViewById(R.id.meta);
                vote = v.findViewById(R.id.vote);
            }
        }

        @NonNull @Override public H onCreateViewHolder(@NonNull ViewGroup p, int t) {
            return new H(LayoutInflater.from(p.getContext()).inflate(R.layout.item_problem, p, false));
        }

        @Override public void onBindViewHolder(@NonNull H h, int pos) {
            Problem p = data.get(pos);
            h.cat.setText(p.category.toUpperCase());
            h.title.setText(p.title); h.desc.setText(p.desc);
            String m = (p.merged > 1 ? p.merged + " similar merged" : "")
                    + (p.solution != null ? (p.merged > 1 ? "  •  " : "") + "✔ Solved" : "");
            h.meta.setText(m);
            h.meta.setVisibility(m.isEmpty() ? View.INVISIBLE : View.VISIBLE);
            h.vote.setText((p.voted ? "▲ " : "△ ") + p.votes);
            h.vote.setOnClickListener(x -> {
                p.voted = !p.voted; p.votes += p.voted ? 1 : -1;
                h.vote.setText((p.voted ? "▲ " : "△ ") + p.votes);
                h.vote.animate().scaleX(1.35f).scaleY(1.35f).setDuration(120)
                        .withEndAction(() -> h.vote.animate().scaleX(1f).scaleY(1f).setDuration(160)).start();
            });
            h.itemView.setOnClickListener(x -> {
                Intent in = new Intent(getContext(), DetailActivity.class);
                in.putExtra("id", p.id);
                startActivity(in);
            });
        }

        @Override public int getItemCount() { return data.size(); }
    }
}