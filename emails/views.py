import logging
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Min, Q
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailLog, SenderAccount
from .forms import ComposeEmailForm
from .tasks import send_batch_task, retry_failed_batch


logger = logging.getLogger(__name__)


def staff_required(u):
    return u.is_active and u.is_staff


@user_passes_test(staff_required, login_url='/login/')
def compose_email(request):
    if request.method == 'POST':
        form = ComposeEmailForm(request.POST)
        if form.is_valid():
            recipients = form.get_recipients()
            batch_id = uuid.uuid4()
            batch_label = form.cleaned_data['batch_label']
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']
            template_name = 'email/generic.html'

            logs = []
            for r in recipients:
                logs.append(EmailLog(
                    batch_id=batch_id,
                    batch_label=batch_label,
                    recipient_email=r['email'],
                    recipient_name=r.get('name', ''),
                    subject=subject,
                    message_body=message_body,
                    template_name=template_name,
                    status='pending',
                    sent_by=request.user,
                ))

            EmailLog.objects.bulk_create(logs)

            send_batch_task.delay(str(batch_id))

            count = len(logs)
            messages.success(
                request,
                f'Se programaron {count} correos en el lote '
                f'"{batch_label}". El envío está en progreso.')
            return redirect('email_logs')
    else:
        form = ComposeEmailForm()

    return render(request, 'emails/compose.html', {'form': form})


@user_passes_test(staff_required, login_url='/login/')
def email_logs(request):
    batches = (
        EmailLog.objects
        .values('batch_id')
        .annotate(
            batch_label=Min('batch_label'),
            sent_by_email=Min('sent_by__email'),
            fecha=Min('created_at'),
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending')),
        )
        .order_by('-fecha')
    )

    return render(request, 'emails/log_list.html', {'batches': batches})


@user_passes_test(staff_required, login_url='/login/')
def email_log_detail(request, batch_id):
    logs = EmailLog.objects.filter(batch_id=batch_id).order_by('created_at')

    stats = logs.aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed')),
        pending=Count('id', filter=Q(status='pending')),
    )

    batch_label = logs.first().batch_label if logs.exists() else ''
    first_log = logs.first()
    preview_subject = first_log.subject if first_log else ''
    preview_body = first_log.message_body if first_log else ''
    if first_log:
        try:
            # str(): render_to_string devuelve SafeString y el filtro
            # |escape lo dejaría sin escapar, rompiendo el srcdoc.
            preview_html = str(render_to_string(
                first_log.template_name or 'email/generic.html',
                {'subject': first_log.subject,
                 'message': first_log.message_body},
            ))
        except Exception:
            logger.exception(
                "Preview email falló para batch %s (template=%r); "
                "usando message_body como fallback",
                batch_id, first_log.template_name,
            )
            preview_html = first_log.message_body or ''
    else:
        preview_html = ''

    return render(request, 'emails/log_detail.html', {
        'logs': logs,
        'stats': stats,
        'batch_id': batch_id,
        'batch_label': batch_label,
        'preview_html': preview_html,
        'preview_body': preview_body,
        'preview_subject': preview_subject,
    })


@user_passes_test(staff_required, login_url='/login/')
def email_retry_failed(request, batch_id):
    if request.method == 'POST':
        retry_failed_batch.delay(str(batch_id))
        messages.success(
            request,
            'Reintentando envíos fallidos. '
            'El proceso comenzará en breve.')
    return redirect('email_log_detail', batch_id=batch_id)


@user_passes_test(staff_required, login_url='/login/')
def sender_accounts(request):
    accounts = SenderAccount.objects.all()
    return render(request, 'emails/sender_accounts.html', {
        'accounts': accounts,
    })
