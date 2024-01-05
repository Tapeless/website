from django.http import HttpResponse

def index(request):
    return HttpResponse("hello world! You're at the polls index.")

# Create your views here.
