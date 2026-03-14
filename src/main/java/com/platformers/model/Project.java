package com.platformers.model;

public class Project {
    private int id;
    private String title;
    private String url;
    private String category;
    private String description;
    private String thumbnail;

    public Project() {}

    public Project(int id, String title, String url, String category, String description, String thumbnail) {
        this.id = id;
        this.title = title;
        this.url = url;
        this.category = category;
        this.description = description;
        this.thumbnail = thumbnail;
    }

    // Getters and Setters
    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getThumbnail() {
        return thumbnail;
    }

    public void setThumbnail(String thumbnail) {
        this.thumbnail = thumbnail;
    }
}
