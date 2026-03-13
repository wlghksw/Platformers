package com.platformers.controller;

import com.platformers.model.Project;
import com.platformers.service.ProjectService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class MainController {
    
    @Autowired
    private ProjectService projectService;
    
    @GetMapping("/")
    public String index(Model model) {
        List<Project> projects = projectService.getAllProjects();
        model.addAttribute("projects", projects);
        return "index";
    }
    
    @GetMapping("/portfolio")
    public String portfolio(Model model) {
        List<Project> projects = projectService.getAllProjects();
        List<String> categories = projectService.getCategories();
        model.addAttribute("projects", projects);
        model.addAttribute("categories", categories);
        return "portfolio";
    }
}
