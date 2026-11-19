package com.example.devbridge;

import java.util.ArrayList;
import java.util.List;

public class Problem {
    public int id, votes, merged = 1;
    public String title, desc, category, solution;
    public boolean voted;
    public boolean synced = true;
    public double similarityScore;
    public List<String> comments = new ArrayList<>();

    public Problem(int id, String title, String desc, String category, int votes) {
        this.id = id;
        this.title = title;
        this.desc = desc;
        this.category = category;
        this.votes = votes;
    }
}