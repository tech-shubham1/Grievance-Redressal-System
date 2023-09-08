from django.shortcuts import render

def homepage(request):
    return render(request, "grievance/home_page.html")

