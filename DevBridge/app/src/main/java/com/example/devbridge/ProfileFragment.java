package com.example.devbridge;

import android.content.Intent;
import android.content.res.Configuration;
import android.os.Bundle;
import android.view.*;
import android.widget.TextView;
import androidx.annotation.*;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.fragment.app.Fragment;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.materialswitch.MaterialSwitch;

public class ProfileFragment extends Fragment {
    @Nullable @Override
    public View onCreateView(@NonNull LayoutInflater i, @Nullable ViewGroup c, @Nullable Bundle b) {
        View v = i.inflate(R.layout.fragment_profile, c, false);
        TextView avatar = v.findViewById(R.id.pAvatar), role = v.findViewById(R.id.pRole),
                sub = v.findViewById(R.id.pSub), nP = v.findViewById(R.id.pProblems),
                nV = v.findViewById(R.id.pVotes), nS = v.findViewById(R.id.pSolved);
        MaterialButton switchRole = v.findViewById(R.id.pSwitch), logout = v.findViewById(R.id.pLogout);
        MaterialSwitch dark = v.findViewById(R.id.pDark);

        int votes = 0, solved = 0;
        for (Problem p : Repo.I.items) { votes += p.votes; if (p.solution != null) solved++; }
        nP.setText(String.valueOf(Repo.I.items.size()));
        nV.setText(String.valueOf(votes));
        nS.setText(String.valueOf(solved));

        Runnable paint = () -> {
            avatar.setText(Repo.I.role.substring(0, 1));
            role.setText(Repo.I.role);
            sub.setText(Repo.I.role.equals("Developer")
                    ? "You can publish solutions" : "You can report, upvote and comment");
        };
        paint.run();

        switchRole.setOnClickListener(x -> {
            Repo.I.role = Repo.I.role.equals("User") ? "Developer" : "User";
            paint.run();
        });

        boolean isDark = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
                == Configuration.UI_MODE_NIGHT_YES;
        dark.setChecked(isDark);
        dark.setOnCheckedChangeListener((btn, on) -> AppCompatDelegate.setDefaultNightMode(
                on ? AppCompatDelegate.MODE_NIGHT_YES : AppCompatDelegate.MODE_NIGHT_NO));

        logout.setOnClickListener(x -> {
            Intent in = new Intent(getContext(), WelcomeActivity.class);
            in.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(in);
        });

        v.setAlpha(0f); v.animate().alpha(1f).setDuration(400).start();
        return v;
    }
}