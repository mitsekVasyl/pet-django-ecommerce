from django.shortcuts import render


def home(request):
    print(dir(request))
    print(request.headers)
    print(request.session)
    return render(request, 'home.html')
