package com.discovery.models;

public class DiscoveryRequest {
    private String domain;
    private int threshold;
    private String direction; // "outgoing" or "incoming"

    public DiscoveryRequest() {}

    public DiscoveryRequest(String domain, int threshold, String direction) {
        this.domain = domain;
        this.threshold = threshold;
        this.direction = direction;
    }

    public String getDomain() {
        return domain;
    }

    public void setDomain(String domain) {
        this.domain = domain;
    }

    public int getThreshold() {
        return threshold;
    }

    public void setThreshold(int threshold) {
        this.threshold = threshold;
    }

    public String getDirection() {
        return direction;
    }

    public void setDirection(String direction) {
        this.direction = direction;
    }
}
