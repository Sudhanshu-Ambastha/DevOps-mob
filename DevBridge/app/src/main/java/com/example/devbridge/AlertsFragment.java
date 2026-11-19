package com.example.devbridge;

import android.os.Bundle;
import android.view.*;
import android.widget.*;
import androidx.annotation.*;
import androidx.fragment.app.Fragment;

public class AlertsFragment extends Fragment {
    @Nullable @Override
    public View onCreateView(@NonNull LayoutInflater i, @Nullable ViewGroup c, @Nullable Bundle b) {
        View v = i.inflate(R.layout.fragment_alerts, c, false);
        ListView list = v.findViewById(R.id.list);
        list.setAdapter(new ArrayAdapter<>(requireContext(),
                R.layout.item_alert, R.id.alertText, Repo.I.notifications));
        list.setAlpha(0f); list.setTranslationY(40f);
        list.animate().alpha(1f).translationY(0f).setDuration(450).start();
        return v;
    }
}