from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('user-home/', views.user_home, name='user_home'),
    path('books/', views.book_availability, name='book_availability'),
    path('issue/', views.issue_book, name='issue_book'),
    path('return/<int:tx_id>/', views.return_book, name='return_book'),
    path('pay-fine/<int:tx_id>/', views.pay_fine, name='pay_fine'),
    # Admin Maintenance
    path('dashboard/members/', views.membership_list, name='membership_list'),
    path('dashboard/members/add/', views.membership_add, name='membership_add'),
    path('dashboard/members/<int:member_id>/edit/', views.membership_edit, name='membership_edit'),
    path('dashboard/members/<int:member_id>/delete/', views.membership_delete, name='membership_delete'),

    
    path('dashboard/books/', views.book_list, name='book_list'),
    path('dashboard/books/add/', views.book_add, name='book_add'),
    path('dashboard/books/<int:book_id>/edit/', views.book_edit, name='book_edit'),

    path('dashboard/users/', views.user_list, name='user_list'),
    path('dashboard/users/add/', views.user_add, name='user_add'),
    path('dashboard/users/<int:user_id>/edit/', views.user_edit, name='user_edit'),


# Admin Reports
    path('dashboard/reports/pending-issues/', views.pending_issues, name='pending_issues'),
    path('dashboard/reports/overdue-returns/', views.overdue_returns, name='overdue_returns'),
    path('dashboard/reports/active-issues/', views.active_issues, name='active_issues'),
    path('dashboard/reports/memberships/', views.membership_master_list, name='membership_master_list'),
    path('dashboard/reports/books/', views.book_master_list, name='book_master_list'),

# -----------------------------
# User Reports
# -----------------------------
    path('reports/my-active-issues/', views.my_active_issues, name='my_active_issues'),
    path('reports/my-overdue/', views.my_overdue, name='my_overdue'),

# -----------------------------
# Transaction Helper
# -----------------------------
    path('return-book-list/', views.return_book_list, name='return_book_list'),

]
