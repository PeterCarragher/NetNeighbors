package com.discovery.models;

public class DiscoveredDomain {
    private String domain;
    private long count;

    public DiscoveredDomain() {}

    public DiscoveredDomain(String domain, long count) {
        this.domain = domain;
        this.count = count;
    }

    public String getDomain() {
        return domain;
    }

    public void setDomain(String domain) {
        this.domain = domain;
    }

    public long getCount() {
        return count;
    }

    public void setCount(long count) {
        this.count = count;
    }
}
