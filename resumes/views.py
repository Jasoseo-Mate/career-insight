from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Experience, Resume, CoverLetter
from jobs.models import JobPost # CoverLetter와 연결하기 위해 필요

@login_required
def experience_list(request):
    experiences = request.user.experiences.all()
    context = {'experiences': experiences}
    return render(request, 'resumes/experience_list.html', context)

@login_required
def experience_create(request):
    if request.method == 'POST':
        # 실제 폼 처리 로직 (ModelForm을 사용하는 것이 더 좋습니다.)
        title = request.POST.get('title')
        company = request.POST.get('company')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') # null 허용
        description = request.POST.get('description', '')

        Experience.objects.create(
            user=request.user,
            title=title,
            company=company,
            start_date=start_date,
            end_date=end_date if end_date else None, # 빈 문자열은 None으로 변환
            description=description
        )
        return redirect('resumes:experience_list')
    return render(request, 'resumes/experience_form.html')

@login_required
def experience_update(request, pk):
    experience = get_object_or_404(Experience, pk=pk, user=request.user)
    if request.method == 'POST':
        # 실제 폼 처리 로직
        experience.title = request.POST.get('title')
        experience.company = request.POST.get('company')
        experience.start_date = request.POST.get('start_date')
        experience.end_date = request.POST.get('end_date')
        experience.description = request.POST.get('description', '')
        experience.end_date = experience.end_date if experience.end_date else None # 빈 문자열은 None으로 변환
        experience.save()
        return redirect('resumes:experience_list')
    context = {'experience': experience}
    return render(request, 'resumes/experience_form.html', context)

@login_required
def experience_delete(request, pk):
    experience = get_object_or_404(Experience, pk=pk, user=request.user)
    if request.method == 'POST':
        experience.delete()
        return redirect('resumes:experience_list')
    context = {'experience': experience}
    return render(request, 'resumes/experience_confirm_delete.html', context)


# Resume 관련 뷰
@login_required
def resume_list(request):
    resumes = request.user.resumes.all()
    context = {'resumes': resumes}
    return render(request, 'resumes/resume_list.html', context)

@login_required
def resume_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content', '')
        
        Resume.objects.create(
            user=request.user,
            title=title,
            content=content
        )
        return redirect('resumes:resume_list')
    return render(request, 'resumes/resume_form.html')

@login_required
def resume_update(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        resume.title = request.POST.get('title')
        resume.content = request.POST.get('content', '')
        resume.save()
        return redirect('resumes:resume_list')
    context = {'resume': resume}
    return render(request, 'resumes/resume_form.html', context)

@login_required
def resume_delete(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        resume.delete()
        return redirect('resumes:resume_list')
    context = {'resume': resume}
    return render(request, 'resumes/resume_confirm_delete.html', context)


# CoverLetter 관련 뷰
@login_required
def coverletter_list(request):
    coverletters = request.user.cover_letters.all()
    context = {'coverletters': coverletters}
    return render(request, 'resumes/coverletter_list.html', context)

@login_required
def coverletter_create(request, job_post_pk):
    job_post = get_object_or_404(JobPost, pk=job_post_pk)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content', '')

        CoverLetter.objects.create(
            user=request.user,
            job_post=job_post,
            title=title,
            content=content
        )
        return redirect('resumes:coverletter_list') # 또는 해당 job_post 상세 페이지
    context = {'job_post': job_post}
    return render(request, 'resumes/coverletter_form.html', context)

@login_required
def coverletter_update(request, pk):
    coverletter = get_object_or_404(CoverLetter, pk=pk, user=request.user)
    if request.method == 'POST':
        coverletter.title = request.POST.get('title')
        coverletter.content = request.POST.get('content', '')
        coverletter.save()
        return redirect('resumes:coverletter_list')
    context = {'coverletter': coverletter}
    return render(request, 'resumes/coverletter_form.html', context)

@login_required
def coverletter_delete(request, pk):
    coverletter = get_object_or_404(CoverLetter, pk=pk, user=request.user)
    if request.method == 'POST':
        coverletter.delete()
        return redirect('resumes:coverletter_list')
    context = {'coverletter': coverletter}
    return render(request, 'resumes/coverletter_confirm_delete.html', context)
