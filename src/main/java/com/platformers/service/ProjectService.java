package com.platformers.service;

import com.platformers.model.Project;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;

@Service
public class ProjectService {
    
    public List<Project> getAllProjects() {
        return Arrays.asList(
            new Project(3, "입찰공고모니터링", 
                       "https://service.crayonschool.co.kr/admin/crawler/?deadline=&page=1", 
                       "웹사이트", 
                       "입찰 공고 모니터링 프로젝트", 
                       "/assets/bidmonitor.png"),
            new Project(2, "버스킹고", 
                       "https://busking-go-dev.azurewebsites.net/", 
                       "웹사이트", 
                       "버스킹고 프로젝트", 
                       "/assets/buskinggo.png"),
            new Project(1, "컬처쇼크", 
                       "https://cultureshock-dev.azurewebsites.net/", 
                       "웹사이트", 
                       "컬처쇼크 프로젝트", 
                       "/assets/cultureshock.png")
        );
    }
    
    public List<String> getCategories() {
        return Arrays.asList("전체", "웹사이트");
    }
}
