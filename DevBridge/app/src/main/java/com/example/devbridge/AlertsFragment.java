package com.example.devbridge;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ListView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

public class AlertsFragment extends Fragment {
    private ArrayAdapter<String> adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater i, @Nullable ViewGroup c, @Nullable Bundle b) {
        View v = i.inflate(R.layout.fragment_alerts, c, false);
        ListView list = v.findViewById(R.id.list);
        adapter = new ArrayAdapter<>(
                requireContext(),
                R.layout.item_alert,
                R.id.alertText,
                Repo.I.notifications
        );
        list.setAdapter(adapter);
        list.setAlpha(0f);
        list.setTranslationY(40f);
        list.animate().alpha(1f).translationY(0f).setDuration(450).start();
        return v;
    }

    @Override
    public void onResume() {
        super.onResume();
        if (adapter != null) {
            adapter.notifyDataSetChanged();
        }
    }
}