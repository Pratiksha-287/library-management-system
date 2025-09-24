# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from .models import Book, Transaction, Member
from .forms import BookSearchForm, IssueForm, ReturnForm

# configurable constants
LOAN_DAYS = 14
FINE_PER_DAY = Decimal('5.00')


@login_required
def home(request):
    if request.user.is_staff:
        return redirect('admin_home')
    return redirect('user_home')


@login_required
def admin_home(request):
    books_count = Book.objects.count()
    issued_count = Transaction.objects.filter(status='issued').count()
    recent_tx = Transaction.objects.order_by('-issue_date')[:8]
    return render(request, 'library/admin_home.html', {
        'books_count': books_count,
        'issued_count': issued_count,
        'recent_tx': recent_tx,
    })


@login_required
def user_home(request):
    my_issued = Transaction.objects.filter(user=request.user).order_by('-issue_date')
    return render(request, 'library/user_home.html', {'my_issued': my_issued})


@login_required
def book_availability(request):
    form = BookSearchForm(request.GET or None)
    books = Book.objects.all().order_by('title')
    if form.is_valid() and form.cleaned_data.get('q'):
        q = form.cleaned_data['q']
        books = books.filter(title__icontains=q)
    return render(request, 'library/book_availability.html', {'books': books, 'form': form})


@login_required
def issue_book(request):
    # allow GET ?book=<id> to preselect a book from listing
    preselect_id = request.GET.get('book')
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data['book']
            target_user = form.cleaned_data.get('user') or request.user

            # Check availability
            if book.available_copies <= 0:
                messages.error(request, "Book is not available for issuing.")
                return redirect('book_availability')

            # Issue within atomic transaction
            with db_transaction.atomic():
                # decrease available copies
                if book.available_copies <= 0:
                    messages.error(request, "Book became unavailable. Try again.")
                    return redirect('book_availability')
                book.available_copies = book.available_copies - 1
                book.save()

                issue_date = date.today()
                due_date = issue_date + timedelta(days=LOAN_DAYS)
                tx = Transaction.objects.create(
                    user=target_user,
                    book=book,
                    issue_date=issue_date,
                    due_date=due_date
                )

            messages.success(request, f"Issued '{book.title}' to {target_user.username}. Due on {due_date}.")
            # If staff issued and not issuing to self, redirect to admin home, else user_home
            if request.user.is_staff and target_user != request.user:
                return redirect('admin_home')
            return redirect('user_home')
    else:
        initial = {}
        if preselect_id:
            try:
                pre_book = Book.objects.get(id=preselect_id)
                initial['book'] = pre_book
            except Book.DoesNotExist:
                pass
        form = IssueForm(initial=initial)

    # Make user field hidden or not shown for normal users in template.
    return render(request, 'library/issue_book.html', {'form': form})


@login_required
def return_book(request, tx_id):
    tx = get_object_or_404(Transaction, id=tx_id)

    # If non-staff, ensure the transaction belongs to current user.
    if not request.user.is_staff and tx.user != request.user:
        messages.error(request, "You are not authorized to return this transaction.")
        return redirect('user_home')

    if tx.status != 'issued':
        messages.info(request, "This transaction is already returned.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    if request.method == 'POST':
        tx.return_date = date.today()
        tx.fine = tx.calculate_fine(per_day=FINE_PER_DAY)
        tx.status = 'returned'
        tx.save()

        # increment book copies in atomic block
        with db_transaction.atomic():
            book = tx.book
            book.available_copies = book.available_copies + 1
            # safeguard: don't exceed total_copies
            if book.available_copies > book.total_copies:
                book.available_copies = book.total_copies
            book.save()

        if tx.fine > 0:
            messages.warning(request, f"Book returned. Fine due: ₹{tx.fine}. Use Pay Fine to mark payment.")
        else:
            messages.success(request, "Book returned successfully. No fine.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    return render(request, 'library/confirm_return.html', {'tx': tx})


@login_required
def pay_fine(request, tx_id):
    tx = get_object_or_404(Transaction, id=tx_id)

    # Only the transaction owner or staff can pay fines
    if not request.user.is_staff and tx.user != request.user:
        messages.error(request, "You are not authorized to pay this fine.")
        return redirect('user_home')

    if tx.fine <= 0:
        messages.info(request, "No fine due for this transaction.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    if request.method == 'POST':
        # Simulated payment: mark paid
        tx.fine_paid = True
        tx.save()
        messages.success(request, f"Fine of ₹{tx.fine} marked as paid.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    return render(request, 'library/pay_fine.html', {'tx': tx})


# -----------------------------
# Admin Maintenance
# -----------------------------
@staff_member_required
def membership_list(request):
    members = Member.objects.all()
    return render(request, 'library/admin/membership_list.html', {'members': members})

@staff_member_required
def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/admin/book_list.html', {'books': books})

@staff_member_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'library/admin/user_list.html', {'users': users})

# -----------------------------
# Admin Reports
# -----------------------------
@staff_member_required
def pending_issues(request):
    txs = Transaction.objects.filter(status='issued')  # adjust filter if you implement request field
    return render(request, 'library/admin/pending_issues.html', {'txs': txs})

@staff_member_required
def overdue_returns(request):
    today = date.today()
    txs = Transaction.objects.filter(status='issued', due_date__lt=today)
    return render(request, 'library/admin/overdue_returns.html', {'txs': txs})

@staff_member_required
def active_issues(request):
    txs = Transaction.objects.filter(status='issued')
    return render(request, 'library/admin/active_issues.html', {'txs': txs})

@staff_member_required
def membership_master_list(request):
    members = Member.objects.all()
    return render(request, 'library/admin/membership_master_list.html', {'members': members})

@staff_member_required
def book_master_list(request):
    books = Book.objects.all()
    return render(request, 'library/admin/book_master_list.html', {'books': books})

# -----------------------------
# User Reports
# -----------------------------
@login_required
def my_active_issues(request):
    txs = Transaction.objects.filter(user=request.user, status='issued')
    return render(request, 'library/user/my_active_issues.html', {'txs': txs})

@login_required
def my_overdue(request):
    today = date.today()
    txs = Transaction.objects.filter(user=request.user, status='issued', due_date__lt=today)
    return render(request, 'library/user/my_overdue.html', {'txs': txs})

# -----------------------------
# Transaction Helper: Return Book List
# -----------------------------
@login_required
def return_book_list(request):
    if request.user.is_staff:
        txs = Transaction.objects.filter(status='issued')
    else:
        txs = Transaction.objects.filter(user=request.user, status='issued')
    return render(request, 'library/return_book_list.html', {'txs': txs})
