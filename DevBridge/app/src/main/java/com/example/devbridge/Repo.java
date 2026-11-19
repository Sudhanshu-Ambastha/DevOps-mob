package com.example.devbridge;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.os.Looper;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

import retrofit2.Response;

public class Repo {
    public static final Repo I = new Repo();
    public final List<Problem> items = new ArrayList<>();
    public final List<String> notifications = new ArrayList<>();
    public String role = "User";

    private DbHelper db;
    private int next = 1;

    private final ExecutorService syncExecutor = Executors.newSingleThreadExecutor();
    private final AtomicBoolean isSyncing = new AtomicBoolean(false);
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    public interface SyncCallback {
        void onSyncFinished(int syncedCount, int remainingCount);
    }

    private Repo() {
        seedInMemoryDefaults();
    }

    private void seedInMemoryDefaults() {
        items.clear();
        notifications.clear();
        next = 1;
        items.add(new Problem(next++, "Live city bus tracking",
                "I cannot tell when my bus will arrive. Show live location. Send arrival alerts.",
                "Transport", 24));
        items.add(new Problem(next++, "Hostel mess menu app",
                "Students never know the daily mess menu. Let students rate meals.",
                "Campus", 17));
        items.add(new Problem(next++, "Local doctor appointment slots",
                "Clinics have no online booking. Show free slots. Remind patients.",
                "Health", 9));
        notifications.add("Welcome to DevBridge! Submit a problem or upvote existing ones.");
    }

    /** Call once in SplashActivity / MainActivity with any Context. */
    public void init(Context context) {
        if (context == null || this.db != null) return;
        this.db = new DbHelper(context.getApplicationContext());

        if (db.isEmpty()) {
            for (Problem p : items) {
                p.synced = true;
                db.insertProblem(p);
            }
            for (String n : notifications) {
                db.insertNotification(n);
            }
        }
        reloadFromDb();
    }

    public void reloadFromDb() {
        if (db == null) return;
        items.clear();
        items.addAll(db.getAllProblems());

        notifications.clear();
        notifications.addAll(db.getNotifications());

        int maxId = 0;
        for (Problem p : items) {
            if (p.id > maxId) maxId = p.id;
        }
        next = maxId + 1;
    }

    public Problem byId(int id) {
        for (Problem p : items) if (p.id == id) return p;
        return null;
    }

    public void addNote(String s) {
        notifications.add(0, s);
        if (db != null) db.insertNotification(s);
    }

    public void addComment(Problem p, String commentText) {
        if (p == null) return;
        p.comments.add(commentText);
        if (db != null) db.insertComment(p.id, commentText, false);
    }

    public void toggleVote(Problem p) {
        if (p == null) return;
        p.voted = !p.voted;
        p.votes += p.voted ? 1 : -1;
        p.synced = false;
        if (db != null) db.updateProblem(p);
    }

    private Set<String> tokens(String s) {
        Set<String> t = new HashSet<>();
        for (String w : s.toLowerCase().split("[^a-z]+")) if (w.length() > 3) t.add(w);
        return t;
    }

    public Problem findSimilar(String text) {
        Set<String> a = tokens(text);
        if (a.isEmpty()) return null;
        Problem best = null;
        double bestScore = 0.2;
        for (Problem p : items) {
            Set<String> b = tokens(p.title + " " + p.desc);
            Set<String> inter = new HashSet<>(a);
            inter.retainAll(b);
            Set<String> union = new HashSet<>(a);
            union.addAll(b);
            double s = (double) inter.size() / union.size();
            if (s > bestScore) {
                bestScore = s;
                best = p;
            }
        }
        return best;
    }

    public boolean submit(String title, String desc) {
        Problem m = findSimilar(title + " " + desc);
        if (m != null) {
            m.votes++;
            m.merged++;
            m.synced = false;
            if (db != null) db.updateProblem(m);
            addNote("Your report was merged into: " + m.title);
            return true;
        }
        Problem created = new Problem(next++, title, desc, "General", 1);
        created.synced = false;
        if (db != null) db.insertProblem(created);
        items.add(created);
        addNote("Problem submitted: " + title);
        return false;
    }

    public boolean isOnline(Context context) {
        if (context == null) return false;
        ConnectivityManager cm = (ConnectivityManager)
                context.getApplicationContext().getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm == null) return false;
        Network active = cm.getActiveNetwork();
        if (active == null) return false;
        NetworkCapabilities caps = cm.getNetworkCapabilities(active);
        return caps != null && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    }

    public void syncPending(Context context) {
        syncPending(context, null);
    }

    public void syncPending(Context context, SyncCallback callback) {
        if (db == null || context == null || !isOnline(context)) {
            if (callback != null) {
                int rem = db != null ? db.getUnsyncedProblems().size() : 0;
                callback.onSyncFinished(0, rem);
            }
            return;
        }
        if (!isSyncing.compareAndSet(false, true)) {
            return;
        }

        syncExecutor.execute(() -> {
            int syncedNow = 0;
            try {
                List<Problem> pending = db.getUnsyncedProblems();
                for (Problem p : pending) {
                    try {
                        Response<Problem> res = RetrofitClient.getService().syncProblem(p).execute();
                        if (res.isSuccessful()) {
                            Problem serverItem = res.body();
                            if (serverItem != null && serverItem.category != null && !serverItem.category.isEmpty()) {
                                p.category = serverItem.category;
                            }
                            p.synced = true;
                            db.updateProblem(p);
                            db.markProblemSynced(p.id);
                            syncedNow++;
                        }
                    } catch (Exception ignored) {
                        // Keep p.synced == false so it retries later
                    }
                }

                int remaining = db.getUnsyncedProblems().size();
                final int finalSynced = syncedNow;
                mainHandler.post(() -> {
                    reloadFromDb();
                    if (callback != null) {
                        callback.onSyncFinished(finalSynced, remaining);
                    }
                });
            } finally {
                isSyncing.set(false);
            }
        });
    }

    public String generateSrs(Problem p) {
        StringBuilder sb = new StringBuilder("SRS: " + p.title + "\n\n1. Purpose\n" + p.desc + "\n\n2. Functional Requirements\n");
        int n = 1;
        for (String s : p.desc.split("[.!?]\\s*")) if (!s.trim().isEmpty())
            sb.append("FR").append(n++).append(": The system shall address: ").append(s.trim()).append(".\n");
        sb.append("\n3. Non-Functional\nNFR1: Responses under 2 seconds.\nNFR2: Android 8.0+.\n\n4. Demand\n")
                .append(p.votes).append(" upvotes, ").append(p.merged).append(" merged reports.");
        return sb.toString();
    }
}