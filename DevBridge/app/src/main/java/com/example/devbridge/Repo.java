package com.example.devbridge;

import java.util.*;

/** In-memory store. Swap these methods for Retrofit calls to your FastAPI backend later. */
public class Repo {
    public static final Repo I = new Repo();
    public final List<Problem> items = new ArrayList<>();
    public final List<String> notifications = new ArrayList<>();
    public String role = "User";
    private int next = 1;

    private Repo() {
        items.add(new Problem(next++, "Live city bus tracking", "I cannot tell when my bus will arrive. Show live location. Send arrival alerts.", "Transport", 24));
        items.add(new Problem(next++, "Hostel mess menu app", "Students never know the daily mess menu. Let students rate meals.", "Campus", 17));
        items.add(new Problem(next++, "Local doctor appointment slots", "Clinics have no online booking. Show free slots. Remind patients.", "Health", 9));
        notifications.add("Welcome to DevBridge! Submit a problem or upvote existing ones.");
    }

    public Problem byId(int id) {
        for (Problem p : items) if (p.id == id) return p;
        return null;
    }

    public void addNote(String s) { notifications.add(0, s); }

    private Set<String> tokens(String s) {
        Set<String> t = new HashSet<>();
        for (String w : s.toLowerCase().split("[^a-z]+")) if (w.length() > 3) t.add(w);
        return t;
    }

    /** Jaccard similarity on keywords. Returns best match above threshold, or null. */
    public Problem findSimilar(String text) {
        Set<String> a = tokens(text);
        if (a.isEmpty()) return null;
        Problem best = null; double bestScore = 0.2;
        for (Problem p : items) {
            Set<String> b = tokens(p.title + " " + p.desc);
            Set<String> inter = new HashSet<>(a); inter.retainAll(b);
            Set<String> union = new HashSet<>(a); union.addAll(b);
            double s = (double) inter.size() / union.size();
            if (s > bestScore) { bestScore = s; best = p; }
        }
        return best;
    }

    /** Returns true if merged into an existing problem. */
    public boolean submit(String title, String desc) {
        Problem m = findSimilar(title + " " + desc);
        if (m != null) {
            m.votes++; m.merged++;
            addNote("Your report was merged into: " + m.title);
            return true;
        }
        items.add(new Problem(next++, title, desc, "General", 1));
        addNote("Problem submitted: " + title);
        return false;
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