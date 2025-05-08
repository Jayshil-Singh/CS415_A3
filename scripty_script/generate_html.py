import os

# Define the HTML content for each page
# NOTE: The HTML content is truncated here for brevity in this example.
# In the actual generated script, the full HTML for each page will be included.

html_content = {
    "login.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .flash-message {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0.375rem; /* rounded-md */
            font-size: 0.875rem; /* text-sm */
        }
        .flash-success { background-color: #d1fae5; color: #065f46; } /* green-100, green-800 */
        .flash-error { background-color: #fee2e2; color: #991b1b; } /* red-100, red-800 */
        .flash-info { background-color: #dbeafe; color: #1e40af; } /* blue-100, blue-800 */
    </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-2xl">
        <div class="text-center">
            <img src="https://placehold.co/100x100/003366/FFFFFF?text=USP" alt="USP Logo" class="mx-auto mb-4 rounded-full">
            <h1 class="text-3xl font-bold text-gray-800">Student Login</h1>
            <p class="text-gray-600">Welcome back to the USP Enrollment System</p>
        </div>

        <form class="space-y-6" action="#" method="POST"> <div>
                <label for="email" class="block text-sm font-medium text-gray-700">Email address</label>
                <div class="mt-1">
                    <input id="email" name="email" type="email" autocomplete="email" required
                           class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                           placeholder="you@example.com">
                </div>
            </div>

            <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <div class="mt-1 relative">
                    <input id="password" name="password" type="password" autocomplete="current-password" required
                           class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                           placeholder="••••••••">
                    </div>
            </div>

            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <input id="remember-me" name="remember-me" type="checkbox"
                           class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
                    <label for="remember-me" class="ml-2 block text-sm text-gray-900">Remember me</label>
                </div>
                <div class="text-sm">
                    <a href="#" class="font-medium text-indigo-600 hover:text-indigo-500">Forgot your password?</a>
                </div>
            </div>

            <div>
                <button type="submit"
                        class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out">
                    <i class="fas fa-sign-in-alt mr-2"></i>Sign in
                </button>
            </div>
        </form>

        <p class="mt-8 text-sm text-center text-gray-600">
            Don't have an account?
            <a href="register.html" class="font-medium text-indigo-600 hover:text-indigo-500">Register here</a>
        </p>
    </div>
</body>
</html>
""",
    "register.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .flash-message {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0.375rem; /* rounded-md */
            font-size: 0.875rem; /* text-sm */
        }
        .flash-success { background-color: #d1fae5; color: #065f46; }
        .flash-error { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen py-12">
    <div class="w-full max-w-lg p-8 space-y-6 bg-white rounded-xl shadow-2xl">
        <div class="text-center">
            <img src="https://placehold.co/100x100/003366/FFFFFF?text=USP" alt="USP Logo" class="mx-auto mb-4 rounded-full">
            <h1 class="text-3xl font-bold text-gray-800">Create Student Account</h1>
            <p class="text-gray-600">Join the USP Enrollment System</p>
        </div>

        <form class="space-y-5" action="#" method="POST"> <div>
                <label for="full_name" class="block text-sm font-medium text-gray-700">Full Name</label>
                <input id="full_name" name="full_name" type="text" required
                       class="w-full px-4 py-3 mt-1 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                       placeholder="John Doe">
            </div>

            <div>
                <label for="student_id" class="block text-sm font-medium text-gray-700">Student ID</label>
                <input id="student_id" name="student_id" type="text" required
                       class="w-full px-4 py-3 mt-1 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                       placeholder="S12345678">
            </div>

            <div>
                <label for="email" class="block text-sm font-medium text-gray-700">Email Address</label>
                <input id="email" name="email" type="email" autocomplete="email" required
                       class="w-full px-4 py-3 mt-1 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                       placeholder="you@example.com">
            </div>

            <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <input id="password" name="password" type="password" autocomplete="new-password" required
                       class="w-full px-4 py-3 mt-1 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                       placeholder="••••••••">
            </div>
             <div>
                <label for="confirm_password" class="block text-sm font-medium text-gray-700">Confirm Password</label>
                <input id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" required
                       class="w-full px-4 py-3 mt-1 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                       placeholder="••••••••">
            </div>

            <div>
                <label for="programme" class="block text-sm font-medium text-gray-700">Programme</label>
                <select id="programme" name="programme" required
                        class="w-full px-4 py-3 mt-1 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                    <option value="" disabled selected>Select your programme</option>
                    <option value="bsc_cs">Bachelor of Science in Computer Science</option>
                    <option value="ba_eng">Bachelor of Arts in English</option>
                    <option value="bcomm_acc">Bachelor of Commerce in Accounting</option>
                    <option value="dip_it">Diploma in Information Technology</option>
                    <option value="cert_bus">Certificate in Business Studies</option>
                </select>
            </div>

            <div>
                <button type="submit"
                        class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out">
                    <i class="fas fa-user-plus mr-2"></i>Register
                </button>
            </div>
        </form>

        <p class="mt-8 text-sm text-center text-gray-600">
            Already have an account?
            <a href="login.html" class="font-medium text-indigo-600 hover:text-indigo-500">Login here</a>
        </p>
    </div>
</body>
</html>
""",
    "dashboard.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .flash-message { padding: 1rem; margin-bottom: 1rem; border-radius: 0.375rem; font-size: 0.875rem; }
        .flash-success { background-color: #d1fae5; color: #065f46; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a href="dashboard.html" class="flex-shrink-0">
                        <img class="h-10 w-auto" src="https://placehold.co/150x50/003366/FFFFFF?text=USP+Enroll" alt="USP Logo">
                    </a>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a href="dashboard.html" class="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm font-medium" aria-current="page">Dashboard</a>
                            <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Enroll</a>
                            <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">My Enrollment</a>
                            <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Fees</a>
                            <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Programmes</a>
                        </div>
                    </div>
                </div>
                <div class="hidden md:block">
                    <div class="ml-4 flex items-center md:ml-6">
                        <a href="profile.html" class="p-1 rounded-full text-gray-500 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-white" title="Profile">
                            <span class="sr-only">View profile</span>
                            <i class="fas fa-user-circle fa-lg"></i>
                        </a>
                        <a href="login.html" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-button" class="bg-gray-50 inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white" aria-controls="mobile-menu" aria-expanded="false">
                        <span class="sr-only">Open main menu</span>
                        <i class="fas fa-bars fa-lg"></i>
                    </button>
                </div>
            </div>
        </div>
        <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                <a href="dashboard.html" class="bg-indigo-600 text-white block px-3 py-2 rounded-md text-base font-medium" aria-current="page">Dashboard</a>
                <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Enroll</a>
                <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">My Enrollment</a>
                <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Fees</a>
                <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Programmes</a>
            </div>
            <div class="pt-4 pb-3 border-t border-gray-200">
                <div class="flex items-center px-5">
                    <div class="flex-shrink-0">
                         <img class="h-10 w-10 rounded-full" src="https://placehold.co/40x40/E0E0E0/757575?text=S" alt="User Avatar">
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium leading-none text-gray-800">Ratu Epeli Nailatikau</div> <div class="text-sm font-medium leading-none text-gray-500">s11223344@student.usp.ac.fj</div> </div>
                </div>
                <div class="mt-3 px-2 space-y-1">
                    <a href="profile.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-user-edit mr-2"></i>Your Profile</a>
                    <a href="login.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-sign-out-alt mr-2"></i>Sign out</a>
                </div>
            </div>
        </div>
    </nav>

    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-semibold text-gray-900">Student Dashboard</h1>
        </div>
    </header>

    <main>
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="bg-indigo-600 text-white p-6 rounded-lg shadow-md mb-8">
                <h2 class="text-3xl font-bold">Welcome, Ratu Epeli Nailatikau!</h2> <p class="mt-2 text-indigo-200">Here's a quick overview of your academic journey. Select an option below to get started.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <a href="enroll.html" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center space-x-4">
                        <div class="bg-green-500 p-3 rounded-full text-white">
                            <i class="fas fa-book-medical fa-2x"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-800">Course Enrollment</h3>
                            <p class="text-gray-600 text-sm">Enroll in new courses for the upcoming semester.</p>
                        </div>
                    </div>
                </a>

                <a href="enrollment.html" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center space-x-4">
                        <div class="bg-blue-500 p-3 rounded-full text-white">
                            <i class="fas fa-clipboard-list fa-2x"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-800">Current Enrollment</h3>
                            <p class="text-gray-600 text-sm">View your currently enrolled courses and manage them.</p>
                        </div>
                    </div>
                </a>

                <a href="fees.html" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center space-x-4">
                        <div class="bg-yellow-500 p-3 rounded-full text-white">
                            <i class="fas fa-dollar-sign fa-2x"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-800">Fees & Holds</h3>
                            <p class="text-gray-600 text-sm">Check your tuition fees and any academic holds.</p>
                        </div>
                    </div>
                </a>

                <a href="programmes.html" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center space-x-4">
                        <div class="bg-purple-500 p-3 rounded-full text-white">
                            <i class="fas fa-graduation-cap fa-2x"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-800">Programme Details</h3>
                            <p class="text-gray-600 text-sm">Explore programme structures and course information.</p>
                        </div>
                    </div>
                </a>
                
                <a href="profile.html" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center space-x-4">
                        <div class="bg-teal-500 p-3 rounded-full text-white">
                            <i class="fas fa-user-cog fa-2x"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-800">Profile & Settings</h3>
                            <p class="text-gray-600 text-sm">Update your personal information and preferences.</p>
                        </div>
                    </div>
                </a>

                <a href="login.html" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1 md:col-span-1 lg:col-span-1">
                     <div class="flex items-center space-x-4">
                        <div class="bg-red-500 p-3 rounded-full text-white">
                            <i class="fas fa-sign-out-alt fa-2x"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-800">Logout</h3>
                            <p class="text-gray-600 text-sm">Sign out of the enrollment system.</p>
                        </div>
                    </div>
                </a>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
            &copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System. All rights reserved.
        </div>
    </footer>

    <script>
        // Basic mobile menu toggle
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    </script>
</body>
</html>
""",
    "enroll.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Enrollment - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .flash-message { padding: 1rem; margin-bottom: 1rem; border-radius: 0.375rem; font-size: 0.875rem; }
        .flash-success { background-color: #d1fae5; color: #065f46; }
        .flash-error { background-color: #fee2e2; color: #991b1b; }
        .flash-info { background-color: #dbeafe; color: #1e40af; }
        .loading-spinner-container { display: flex; justify-content: center; align-items: center; height: 200px; }
        .loading-spinner {
            border: 4px solid rgba(0, 0, 0, .1);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border-left-color: #4f46e5; /* indigo-600 */
            animation: spin 1s ease infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .course-prereq-met { color: green; }
        .course-prereq-unmet { color: red; font-weight: bold; }
        .course-disabled { opacity: 0.6; cursor: not-allowed; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a href="dashboard.html" class="flex-shrink-0">
                        <img class="h-10 w-auto" src="https://placehold.co/150x50/003366/FFFFFF?text=USP+Enroll" alt="USP Logo">
                    </a>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                            <a href="enroll.html" class="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm font-medium" aria-current="page">Enroll</a>
                            <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">My Enrollment</a>
                            <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Fees</a>
                            <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Programmes</a>
                        </div>
                    </div>
                </div>
                <div class="hidden md:block">
                     <div class="ml-4 flex items-center md:ml-6">
                        <a href="profile.html" class="p-1 rounded-full text-gray-500 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-white" title="Profile">
                            <span class="sr-only">View profile</span>
                            <i class="fas fa-user-circle fa-lg"></i>
                        </a>
                        <a href="login.html" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-button" class="bg-gray-50 inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white" aria-controls="mobile-menu" aria-expanded="false">
                        <span class="sr-only">Open main menu</span>
                        <i class="fas fa-bars fa-lg"></i>
                    </button>
                </div>
            </div>
        </div>
         <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Dashboard</a>
                <a href="enroll.html" class="bg-indigo-600 text-white block px-3 py-2 rounded-md text-base font-medium" aria-current="page">Enroll</a>
                <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">My Enrollment</a>
                <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Fees</a>
                <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Programmes</a>
            </div>
            <div class="pt-4 pb-3 border-t border-gray-200">
                <div class="flex items-center px-5">
                    <div class="flex-shrink-0">
                         <img class="h-10 w-10 rounded-full" src="https://placehold.co/40x40/E0E0E0/757575?text=S" alt="User Avatar">
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium leading-none text-gray-800">Ratu Epeli Nailatikau</div>
                        <div class="text-sm font-medium leading-none text-gray-500">s11223344@student.usp.ac.fj</div>
                    </div>
                </div>
                <div class="mt-3 px-2 space-y-1">
                    <a href="profile.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-user-edit mr-2"></i>Your Profile</a>
                    <a href="login.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-sign-out-alt mr-2"></i>Sign out</a>
                </div>
            </div>
        </div>
    </nav>

    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-semibold text-gray-900">Course Enrollment</h1>
        </div>
    </header>

    <main>
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="bg-white p-6 rounded-lg shadow-md">
                <div class="mb-6">
                    <label for="semester" class="block text-sm font-medium text-gray-700 mb-1">Select Semester:</label>
                    <select id="semester" name="semester" class="w-full md:w-1/2 lg:w-1/3 px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                        <option value="sem1_2025">Semester 1, 2025</option>
                        <option value="sem2_2025">Semester 2, 2025</option>
                        <option value="sem1_2026">Semester 1, 2026</option>
                    </select>
                    <p class="text-sm text-gray-500 mt-2">Courses will load based on your programme and selected semester.</p>
                </div>

                <div id="loading-courses" class="loading-spinner-container hidden">
                    <div class="loading-spinner"></div>
                    <p class="ml-3 text-gray-600">Loading courses...</p>
                </div>
                
                <div id="course-list-container">
                    <h3 class="text-xl font-semibold text-gray-800 mb-4">Available Courses for Bachelor of Science in Computer Science</h3>
                    <p class="mb-4 text-sm text-indigo-600"><i class="fas fa-info-circle mr-1"></i> You can select a maximum of 4 courses.</p>
                    
                    <form id="enrollment-form" action="#" method="POST"> <div class="space-y-4">
                            <div class="p-4 border rounded-lg hover:shadow-md transition-shadow">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-semibold text-lg text-gray-800">CS111: Introduction to Computing</h4>
                                        <p class="text-sm text-gray-500">Fundamentals of computer science and programming.</p>
                                    </div>
                                    <input type="checkbox" name="courses" value="CS111" class="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 course-checkbox">
                                </div>
                                <p class="text-xs text-gray-500 mt-1">Prerequisites: None</p>
                            </div>

                            <div class="p-4 border rounded-lg hover:shadow-md transition-shadow">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-semibold text-lg text-gray-800">CS112: Data Structures and Algorithms</h4>
                                        <p class="text-sm text-gray-500">Essential data structures and algorithm analysis.</p>
                                    </div>
                                    <input type="checkbox" name="courses" value="CS112" class="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 course-checkbox">
                                </div>
                                <p class="text-xs mt-1"><span class="course-prereq-met"><i class="fas fa-check-circle mr-1"></i>Prerequisites: CS111 (Met)</span></p>
                            </div>

                            <div class="p-4 border rounded-lg hover:shadow-md transition-shadow course-disabled">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-semibold text-lg text-gray-800">CS241: Operating Systems</h4>
                                        <p class="text-sm text-gray-500">Principles of modern operating systems.</p>
                                    </div>
                                    <input type="checkbox" name="courses" value="CS241" class="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 course-checkbox" disabled>
                                </div>
                                <p class="text-xs mt-1"><span class="course-prereq-unmet"><i class="fas fa-times-circle mr-1"></i>Prerequisites: CS112 (Not Met)</span></p>
                            </div>

                            <div class="p-4 border rounded-lg hover:shadow-md transition-shadow">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-semibold text-lg text-gray-800">MA101: Calculus I</h4>
                                        <p class="text-sm text-gray-500">Introduction to differential and integral calculus.</p>
                                    </div>
                                    <input type="checkbox" name="courses" value="MA101" class="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 course-checkbox">
                                </div>
                                <p class="text-xs text-gray-500 mt-1">Prerequisites: None</p>
                            </div>
                            
                            <div class="p-4 border rounded-lg hover:shadow-md transition-shadow">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-semibold text-lg text-gray-800">IS121: Information Systems I</h4>
                                        <p class="text-sm text-gray-500">Introduction to Information Systems concepts.</p>
                                    </div>
                                    <input type="checkbox" name="courses" value="IS121" class="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 course-checkbox">
                                </div>
                                <p class="text-xs text-gray-500 mt-1">Prerequisites: None</p>
                            </div>
                        </div>

                        <div class="mt-8 text-right">
                            <p class="text-sm text-gray-600 mb-2">Selected courses: <span id="selected-count">0</span>/4</p>
                            <button type="submit" id="enroll-button"
                                    class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                    disabled> <i class="fas fa-check-circle mr-2"></i>Enroll in Selected Courses
                            </button>
                        </div>
                    </form>
                </div>
                 </div>
        </div>
    </main>

    <footer class="bg-white border-t mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
            &copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System. All rights reserved.
        </div>
    </footer>
    <script>
        // Basic mobile menu toggle
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }

        // Course selection limit and button enable/disable
        const checkboxes = document.querySelectorAll('.course-checkbox');
        const selectedCountSpan = document.getElementById('selected-count');
        const enrollButton = document.getElementById('enroll-button');
        const maxCourses = 4;

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const checkedCount = document.querySelectorAll('.course-checkbox:checked').length;
                selectedCountSpan.textContent = checkedCount;

                if (checkedCount > 0 && checkedCount <= maxCourses) {
                    enrollButton.disabled = false;
                    enrollButton.classList.remove('disabled:opacity-50');
                } else {
                    enrollButton.disabled = true;
                    enrollButton.classList.add('disabled:opacity-50');
                }

                if (checkedCount > maxCourses) {
                    // Optionally, provide a more prominent warning or prevent checking
                    alert(`You can select a maximum of ${maxCourses} courses.`);
                    checkbox.checked = false; // Revert the last check
                    selectedCountSpan.textContent = document.querySelectorAll('.course-checkbox:checked').length; // Update count again
                }
            });
        });

        // Simulate loading (for demonstration)
        // document.getElementById('semester').addEventListener('change', () => {
        //     document.getElementById('course-list-container').classList.add('hidden');
        //     document.getElementById('loading-courses').classList.remove('hidden');
        //     setTimeout(() => {
        //         document.getElementById('loading-courses').classList.add('hidden');
        //         document.getElementById('course-list-container').classList.remove('hidden');
        //         // Reset checkboxes and counts if needed
        //     }, 1500);
        // });
    </script>
</body>
</html>
""",
    "enrollment.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Current Enrollment - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .flash-message { padding: 1rem; margin-bottom: 1rem; border-radius: 0.375rem; font-size: 0.875rem; }
        .flash-success { background-color: #d1fae5; color: #065f46; }
        .flash-error { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a href="dashboard.html" class="flex-shrink-0">
                        <img class="h-10 w-auto" src="https://placehold.co/150x50/003366/FFFFFF?text=USP+Enroll" alt="USP Logo">
                    </a>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                            <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Enroll</a>
                            <a href="enrollment.html" class="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm font-medium" aria-current="page">My Enrollment</a>
                            <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Fees</a>
                            <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Programmes</a>
                        </div>
                    </div>
                </div>
                <div class="hidden md:block">
                     <div class="ml-4 flex items-center md:ml-6">
                        <a href="profile.html" class="p-1 rounded-full text-gray-500 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-white" title="Profile">
                            <span class="sr-only">View profile</span>
                            <i class="fas fa-user-circle fa-lg"></i>
                        </a>
                        <a href="login.html" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-button" class="bg-gray-50 inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white" aria-controls="mobile-menu" aria-expanded="false">
                        <span class="sr-only">Open main menu</span>
                        <i class="fas fa-bars fa-lg"></i>
                    </button>
                </div>
            </div>
        </div>
         <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Dashboard</a>
                <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Enroll</a>
                <a href="enrollment.html" class="bg-indigo-600 text-white block px-3 py-2 rounded-md text-base font-medium" aria-current="page">My Enrollment</a>
                <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Fees</a>
                <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Programmes</a>
            </div>
            <div class="pt-4 pb-3 border-t border-gray-200">
                <div class="flex items-center px-5">
                    <div class="flex-shrink-0">
                         <img class="h-10 w-10 rounded-full" src="https://placehold.co/40x40/E0E0E0/757575?text=S" alt="User Avatar">
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium leading-none text-gray-800">Ratu Epeli Nailatikau</div>
                        <div class="text-sm font-medium leading-none text-gray-500">s11223344@student.usp.ac.fj</div>
                    </div>
                </div>
                <div class="mt-3 px-2 space-y-1">
                    <a href="profile.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-user-edit mr-2"></i>Your Profile</a>
                    <a href="login.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-sign-out-alt mr-2"></i>Sign out</a>
                </div>
            </div>
        </div>
    </nav>

    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-semibold text-gray-900">My Current Enrollment</h1>
        </div>
    </header>

    <main>
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="bg-white p-6 rounded-lg shadow-md">
                <h3 class="text-xl font-semibold text-gray-800 mb-6">Your Enrolled Courses for Semester 1, 2025</h3>
                
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course Code</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course Name</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Semester</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">CS111</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">Introduction to Computing</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">Semester 1, 2025</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <button onclick="confirmDrop('CS111', 'Introduction to Computing')" class="text-red-600 hover:text-red-800 transition duration-150 ease-in-out">
                                        <i class="fas fa-trash-alt mr-1"></i>Drop Course
                                    </button>
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">MA101</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">Calculus I</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">Semester 1, 2025</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <button onclick="confirmDrop('MA101', 'Calculus I')" class="text-red-600 hover:text-red-800 transition duration-150 ease-in-out">
                                        <i class="fas fa-trash-alt mr-1"></i>Drop Course
                                    </button>
                                </td>
                            </tr>
                            </tbody>
                    </table>
                </div>

                <div id="no-enrollment-message" class="text-center py-12 hidden"> <i class="fas fa-folder-open fa-4x text-gray-300 mb-4"></i>
                    <p class="text-xl text-gray-700 font-semibold">No Courses Enrolled</p>
                    <p class="text-gray-500 mt-2">You are not currently enrolled in any courses for this semester.</p>
                    <a href="enroll.html" class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        <i class="fas fa-plus-circle mr-2"></i>Enroll in Courses
                    </a>
                </div>
            </div>
        </div>
    </main>

    <div id="confirmation-modal" class="fixed z-50 inset-0 overflow-y-auto hidden" aria-labelledby="modal-title" role="dialog" aria-modal="true">
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div class="sm:flex sm:items-start">
                        <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                            <i class="fas fa-exclamation-triangle text-red-600"></i>
                        </div>
                        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                            <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">Drop Course Confirmation</h3>
                            <div class="mt-2">
                                <p class="text-sm text-gray-500" id="modal-message">Are you sure you want to drop this course? This action cannot be undone.</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button type="button" id="confirm-drop-button" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm">
                        Yes, Drop Course
                    </button>
                    <button type="button" id="cancel-drop-button" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-white border-t mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
            &copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System. All rights reserved.
        </div>
    </footer>
    <script>
        // Basic mobile menu toggle
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }

        // Modal functionality
        const modal = document.getElementById('confirmation-modal');
        const modalMessage = document.getElementById('modal-message');
        const confirmDropButton = document.getElementById('confirm-drop-button');
        const cancelDropButton = document.getElementById('cancel-drop-button');
        let courseToDropCode = '';

        function confirmDrop(courseCode, courseName) {
            courseToDropCode = courseCode;
            modalMessage.textContent = `Are you sure you want to drop ${courseName} (${courseCode})? This action cannot be undone.`;
            modal.classList.remove('hidden');
        }

        confirmDropButton.addEventListener('click', () => {
            // Placeholder for actual drop logic
            console.log(`Dropping course: ${courseToDropCode}`);
            alert(`Course ${courseToDropCode} would be dropped here. Implement backend logic.`);
            // Add flash message simulation here
            modal.classList.add('hidden');
            // Potentially remove the row from the table or reload the page
        });

        cancelDropButton.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        
        // Check if table has rows, if not, show empty state
        // This is a basic check, a more robust solution would check after data is loaded dynamically
        const enrollmentTableBody = document.querySelector('.min-w-full tbody');
        const noEnrollmentMessage = document.getElementById('no-enrollment-message');
        if (enrollmentTableBody && noEnrollmentMessage) {
            if (enrollmentTableBody.rows.length === 0) {
                document.querySelector('.min-w-full').classList.add('hidden'); // Hide table
                noEnrollmentMessage.classList.remove('hidden'); // Show message
            }
        }
    </script>
</body>
</html>
""",
    "fees.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fees & Holds - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a href="dashboard.html" class="flex-shrink-0">
                        <img class="h-10 w-auto" src="https://placehold.co/150x50/003366/FFFFFF?text=USP+Enroll" alt="USP Logo">
                    </a>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                            <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Enroll</a>
                            <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">My Enrollment</a>
                            <a href="fees.html" class="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm font-medium" aria-current="page">Fees</a>
                            <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Programmes</a>
                        </div>
                    </div>
                </div>
                <div class="hidden md:block">
                     <div class="ml-4 flex items-center md:ml-6">
                        <a href="profile.html" class="p-1 rounded-full text-gray-500 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-white" title="Profile">
                            <span class="sr-only">View profile</span>
                            <i class="fas fa-user-circle fa-lg"></i>
                        </a>
                        <a href="login.html" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-button" class="bg-gray-50 inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white" aria-controls="mobile-menu" aria-expanded="false">
                        <span class="sr-only">Open main menu</span>
                        <i class="fas fa-bars fa-lg"></i>
                    </button>
                </div>
            </div>
        </div>
         <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Dashboard</a>
                <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Enroll</a>
                <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">My Enrollment</a>
                <a href="fees.html" class="bg-indigo-600 text-white block px-3 py-2 rounded-md text-base font-medium" aria-current="page">Fees</a>
                <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Programmes</a>
            </div>
            <div class="pt-4 pb-3 border-t border-gray-200">
                <div class="flex items-center px-5">
                    <div class="flex-shrink-0">
                         <img class="h-10 w-10 rounded-full" src="https://placehold.co/40x40/E0E0E0/757575?text=S" alt="User Avatar">
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium leading-none text-gray-800">Ratu Epeli Nailatikau</div>
                        <div class="text-sm font-medium leading-none text-gray-500">s11223344@student.usp.ac.fj</div>
                    </div>
                </div>
                <div class="mt-3 px-2 space-y-1">
                    <a href="profile.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-user-edit mr-2"></i>Your Profile</a>
                    <a href="login.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-sign-out-alt mr-2"></i>Sign out</a>
                </div>
            </div>
        </div>
    </nav>

    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-semibold text-gray-900">Fees & Holds</h1>
        </div>
    </header>

    <main>
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="md:col-span-2 bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">Tuition Fees - Semester 1, 2025</h3>
                    <p class="text-sm text-gray-500 mb-4">Based on 2 enrolled courses (8 units).</p>
                    
                    <div class="space-y-3 mb-6">
                        <div class="flex justify-between items-center py-2 border-b">
                            <span class="text-gray-600">CS111: Introduction to Computing (4 units)</span>
                            <span class="font-medium text-gray-800">FJD 850.00</span>
                        </div>
                        <div class="flex justify-between items-center py-2 border-b">
                            <span class="text-gray-600">MA101: Calculus I (4 units)</span>
                            <span class="font-medium text-gray-800">FJD 850.00</span>
                        </div>
                        <div class="flex justify-between items-center py-2 border-b">
                            <span class="text-gray-600">Student Services Fee</span>
                            <span class="font-medium text-gray-800">FJD 150.00</span>
                        </div>
                        <div class="flex justify-between items-center py-3 text-lg font-semibold">
                            <span class="text-indigo-700">Total Due:</span>
                            <span class="text-indigo-700">FJD 1850.00</span>
                        </div>
                    </div>

                    <div class="mt-6">
                        <h4 class="font-semibold text-gray-700 mb-2">Payment Options:</h4>
                        <ul class="list-disc list-inside text-sm text-gray-600 space-y-1">
                            <li>Online payment via Moodle Pay</li>
                            <li>Bank transfer (details available at Finance Office)</li>
                            <li>In-person payment at USP Cashier</li>
                        </ul>
                        <p class="text-xs text-red-600 mt-3"><i class="fas fa-exclamation-triangle mr-1"></i>Fee payment deadline: 28 February, 2025.</p>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold text-gray-800 mb-4">Status Overview</h3>
                    
                    <div class="mb-6">
                        <p class="text-sm font-medium text-gray-700">Fee Status:</p>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-700">
                            <i class="fas fa-times-circle mr-2"></i>Unpaid
                        </span>
                        </div>

                    <div>
                        <h4 class="text-lg font-semibold text-gray-700 mb-2">Academic Holds:</h4>
                        <div class="p-4 bg-green-50 border-l-4 border-green-500 rounded-r-md">
                             <div class="flex">
                                <div class="flex-shrink-0">
                                   <i class="fas fa-check-circle text-green-500 fa-lg"></i>
                                </div>
                                <div class="ml-3">
                                    <p class="text-sm text-green-700">No active holds on your account. You are clear for enrollment and other services.</p>
                                </div>
                            </div>
                        </div>

                        </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
            &copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System. All rights reserved.
        </div>
    </footer>
    <script>
        // Basic mobile menu toggle
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    </script>
</body>
</html>
""",
    "programmes.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Programmes & Courses - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        [x-cloak] { display: none !important; }
    </style>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a href="dashboard.html" class="flex-shrink-0">
                        <img class="h-10 w-auto" src="https://placehold.co/150x50/003366/FFFFFF?text=USP+Enroll" alt="USP Logo">
                    </a>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                            <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Enroll</a>
                            <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">My Enrollment</a>
                            <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Fees</a>
                            <a href="programmes.html" class="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm font-medium" aria-current="page">Programmes</a>
                        </div>
                    </div>
                </div>
                <div class="hidden md:block">
                     <div class="ml-4 flex items-center md:ml-6">
                        <a href="profile.html" class="p-1 rounded-full text-gray-500 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-white" title="Profile">
                            <span class="sr-only">View profile</span>
                            <i class="fas fa-user-circle fa-lg"></i>
                        </a>
                        <a href="login.html" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-button" class="bg-gray-50 inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white" aria-controls="mobile-menu" aria-expanded="false">
                        <span class="sr-only">Open main menu</span>
                        <i class="fas fa-bars fa-lg"></i>
                    </button>
                </div>
            </div>
        </div>
         <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Dashboard</a>
                <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Enroll</a>
                <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">My Enrollment</a>
                <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Fees</a>
                <a href="programmes.html" class="bg-indigo-600 text-white block px-3 py-2 rounded-md text-base font-medium" aria-current="page">Programmes</a>
            </div>
            <div class="pt-4 pb-3 border-t border-gray-200">
                <div class="flex items-center px-5">
                    <div class="flex-shrink-0">
                         <img class="h-10 w-10 rounded-full" src="https://placehold.co/40x40/E0E0E0/757575?text=S" alt="User Avatar">
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium leading-none text-gray-800">Ratu Epeli Nailatikau</div>
                        <div class="text-sm font-medium leading-none text-gray-500">s11223344@student.usp.ac.fj</div>
                    </div>
                </div>
                <div class="mt-3 px-2 space-y-1">
                    <a href="profile.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-user-edit mr-2"></i>Your Profile</a>
                    <a href="login.html" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-indigo-500 hover:text-white"><i class="fas fa-sign-out-alt mr-2"></i>Sign out</a>
                </div>
            </div>
        </div>
    </nav>

    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-semibold text-gray-900">Programme & Course Browser</h1>
        </div>
    </header>

    <main>
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8" x-data="programmeData()">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="md:col-span-1 bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold text-gray-800 mb-4">Academic Programmes</h3>
                    <ul class="space-y-2">
                        <template x-for="programme in programmes" :key="programme.id">
                            <li>
                                <button @click="selectProgramme(programme.id)" 
                                        :class="{'bg-indigo-100 text-indigo-700 font-semibold': selectedProgrammeId === programme.id, 'hover:bg-gray-100': selectedProgrammeId !== programme.id}"
                                        class="w-full text-left px-4 py-3 rounded-lg transition-colors duration-150">
                                    <i :class="programme.icon" class="mr-2 text-indigo-500"></i>
                                    <span x-text="programme.name"></span>
                                    <i class="fas fa-chevron-right float-right mt-1 text-gray-400" x-show="selectedProgrammeId !== programme.id"></i>
                                    <i class="fas fa-chevron-down float-right mt-1 text-indigo-700" x-show="selectedProgrammeId === programme.id"></i>
                                </button>
                            </li>
                        </template>
                    </ul>
                </div>

                <div class="md:col-span-2 bg-white p-6 rounded-lg shadow-md">
                    <div x-show="!selectedProgrammeId" class="text-center py-10">
                        <i class="fas fa-search fa-3x text-gray-400 mb-4"></i>
                        <p class="text-gray-600 text-lg">Select a programme from the list to view details.</p>
                    </div>

                    <div x-show="selectedProgrammeId" x-cloak>
                        <div x-show="currentProgramme">
                            <h2 class="text-2xl font-bold text-indigo-700 mb-1" x-text="currentProgramme?.name"></h2>
                            <p class="text-gray-600 mb-6" x-text="currentProgramme?.description"></p>
                            
                            <h4 class="text-lg font-semibold text-gray-700 mb-3">Sub-Programmes / Specializations:</h4>
                            <ul class="list-disc list-inside text-gray-600 mb-6 space-y-1 pl-2" x-show="currentProgramme?.subProgrammes?.length > 0">
                                <template x-for="sub in currentProgramme?.subProgrammes" :key="sub">
                                    <li x-text="sub"></li>
                                </template>
                            </ul>
                             <p class="text-gray-500 text-sm mb-6" x-show="!currentProgramme?.subProgrammes || currentProgramme?.subProgrammes?.length === 0">No specific sub-programmes listed.</p>

                            <h3 class="text-xl font-semibold text-gray-800 mb-4">Core Courses</h3>
                            <div class="space-y-4">
                                <template x-for="course in currentProgramme?.courses" :key="course.code">
                                    <div class="p-4 border rounded-lg bg-gray-50 hover:shadow-sm">
                                        <h4 class="font-semibold text-md text-indigo-600" x-text="course.code + ': ' + course.title"></h4>
                                        <p class="text-sm text-gray-600 mt-1" x-text="course.description"></p>
                                        <p class="text-xs text-gray-500 mt-2">
                                            Prerequisites: <span x-text="course.prerequisites || 'None'"></span>
                                        </p>
                                    </div>
                                </template>
                                 <div x-show="!currentProgramme?.courses || currentProgramme?.courses?.length === 0" class="text-center py-6">
                                    <i class="fas fa-info-circle fa-2x text-gray-400 mb-2"></i>
                                    <p class="text-gray-500">No courses listed for this programme.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
            &copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System. All rights reserved.
        </div>
    </footer>
    <script>
        // Basic mobile menu toggle
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }

        // Alpine.js data for programmes
        function programmeData() {
            return {
                selectedProgrammeId: null,
                programmes: [
                    { 
                        id: 'bsc_cs', name: 'Bachelor of Science in Computer Science', icon: 'fas fa-laptop-code',
                        description: 'Prepares students for careers in software development, data science, and IT infrastructure.',
                        subProgrammes: ['Software Engineering Stream', 'Data Science Stream', 'Cybersecurity Stream'],
                        courses: [
                            { code: 'CS111', title: 'Introduction to Computing', description: 'Fundamentals of CS.', prerequisites: 'None' },
                            { code: 'CS112', title: 'Data Structures & Algorithms', description: 'Core data organization.', prerequisites: 'CS111' },
                            { code: 'CS214', title: 'Web Development', description: 'Building modern web apps.', prerequisites: 'CS112' },
                            { code: 'CS241', title: 'Operating Systems', description: 'OS principles.', prerequisites: 'CS112, MA101' }
                        ]
                    },
                    { 
                        id: 'ba_eng', name: 'Bachelor of Arts in English', icon: 'fas fa-book-open',
                        description: 'Explores literature, language, and critical analysis.',
                        subProgrammes: ['Literature Focus', 'Linguistics Focus'],
                        courses: [
                            { code: 'EN101', title: 'Introduction to Literary Studies', description: 'Basic literary concepts.', prerequisites: 'None' },
                            { code: 'EN102', title: 'Academic Writing', description: 'Effective writing skills.', prerequisites: 'None' },
                            { code: 'EN210', title: 'Shakespearean Drama', description: 'Study of Shakespeare.', prerequisites: 'EN101' }
                        ]
                    },
                    { 
                        id: 'bcomm_acc', name: 'Bachelor of Commerce in Accounting', icon: 'fas fa-calculator',
                        description: 'Focuses on financial reporting, auditing, and taxation.',
                        subProgrammes: [],
                        courses: [
                            { code: 'AF101', title: 'Introduction to Accounting & Financial Management Part I', description: 'Basic accounting principles.', prerequisites: 'None' },
                            { code: 'AF102', title: 'Introduction to Accounting & Financial Management Part II', description: 'Further accounting concepts.', prerequisites: 'AF101' },
                            { code: 'AF201', title: 'Managerial Accounting', description: 'Accounting for decision making.', prerequisites: 'AF102' }
                        ]
                    },
                    { 
                        id: 'dip_it', name: 'Diploma in Information Technology', icon: 'fas fa-network-wired',
                        description: 'Provides foundational IT skills for various roles.',
                        subProgrammes: [],
                        courses: [
                            { code: 'ITD01', title: 'IT Fundamentals', description: 'Basic IT concepts.', prerequisites: 'None' },
                            { code: 'ITD02', title: 'Networking Essentials', description: 'Introduction to computer networks.', prerequisites: 'ITD01' },
                            { code: 'ITD03', title: 'Basic Programming', description: 'Introductory programming skills.', prerequisites: 'ITD01' }
                        ]
                    },
                     { 
                        id: 'cert_bus', name: 'Certificate in Business Studies', icon: 'fas fa-briefcase',
                        description: 'Offers fundamental knowledge in business operations and management.',
                        subProgrammes: [],
                        courses: [
                            { code: 'CB101', title: 'Introduction to Business', description: 'Overview of business concepts.', prerequisites: 'None' },
                            { code: 'CB102', title: 'Basic Marketing', description: 'Fundamentals of marketing.', prerequisites: 'None' }
                        ]
                    }
                ],
                currentProgramme: null,
                selectProgramme(id) {
                    if (this.selectedProgrammeId === id) {
                        this.selectedProgrammeId = null; // Toggle off if already selected
                        this.currentProgramme = null;
                    } else {
                        this.selectedProgrammeId = id;
                        this.currentProgramme = this.programmes.find(p => p.id === id);
                    }
                }
            }
        }
    </script>
</body>
</html>
""",
    "profile.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profile & Settings - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .flash-message { padding: 1rem; margin-bottom: 1rem; border-radius: 0.375rem; font-size: 0.875rem; }
        .flash-success { background-color: #d1fae5; color: #065f46; }
        .flash-error { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a href="dashboard.html" class="flex-shrink-0">
                        <img class="h-10 w-auto" src="https://placehold.co/150x50/003366/FFFFFF?text=USP+Enroll" alt="USP Logo">
                    </a>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                            <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Enroll</a>
                            <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">My Enrollment</a>
                            <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Fees</a>
                            <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Programmes</a>
                        </div>
                    </div>
                </div>
                <div class="hidden md:block">
                     <div class="ml-4 flex items-center md:ml-6">
                        <a href="profile.html" class="p-1 rounded-full text-indigo-600 bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-white" title="Profile">
                            <span class="sr-only">View profile</span>
                            <i class="fas fa-user-circle fa-lg"></i>
                        </a>
                        <a href="login.html" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-button" class="bg-gray-50 inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white" aria-controls="mobile-menu" aria-expanded="false">
                        <span class="sr-only">Open main menu</span>
                        <i class="fas fa-bars fa-lg"></i>
                    </button>
                </div>
            </div>
        </div>
         <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                <a href="dashboard.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Dashboard</a>
                <a href="enroll.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Enroll</a>
                <a href="enrollment.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">My Enrollment</a>
                <a href="fees.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Fees</a>
                <a href="programmes.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium">Programmes</a>
            </div>
            <div class="pt-4 pb-3 border-t border-gray-200">
                <div class="flex items-center px-5">
                    <div class="flex-shrink-0">
                         <img class="h-10 w-10 rounded-full" src="https://placehold.co/40x40/E0E0E0/757575?text=S" alt="User Avatar">
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium leading-none text-gray-800">Ratu Epeli Nailatikau</div>
                        <div class="text-sm font-medium leading-none text-gray-500">s11223344@student.usp.ac.fj</div>
                    </div>
                </div>
                <div class="mt-3 px-2 space-y-1">
                    <a href="profile.html" class="bg-indigo-100 text-indigo-700 block px-3 py-2 rounded-md text-base font-medium"><i class="fas fa-user-edit mr-2"></i>Your Profile</a>
                    <a href="login.html" class="text-gray-700 hover:bg-indigo-500 hover:text-white block px-3 py-2 rounded-md text-base font-medium"><i class="fas fa-sign-out-alt mr-2"></i>Sign out</a>
                </div>
            </div>
        </div>
    </nav>

    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-semibold text-gray-900">Profile & Settings</h1>
        </div>
    </header>

    <main>
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold text-gray-800 mb-6 border-b pb-3">Personal Information</h3>
                    <form action="#" method="POST" class="space-y-6"> <div>
                            <label for="full_name" class="block text-sm font-medium text-gray-700">Full Name</label>
                            <input type="text" name="full_name" id="full_name" value="Ratu Epeli Nailatikau" class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                        </div>

                        <div>
                            <label for="student_id" class="block text-sm font-medium text-gray-700">Student ID</label>
                            <input type="text" name="student_id" id="student_id" value="S11223344" readonly class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm bg-gray-100 sm:text-sm cursor-not-allowed">
                        </div>

                        <div>
                            <label for="email" class="block text-sm font-medium text-gray-700">Email Address</label>
                            <input type="email" name="email" id="email" value="s11223344@student.usp.ac.fj" class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                        </div>
                        
                        <div>
                            <label for="programme_display" class="block text-sm font-medium text-gray-700">Programme</label>
                            <input type="text" name="programme_display" id="programme_display" value="Bachelor of Science in Computer Science" readonly class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm bg-gray-100 sm:text-sm cursor-not-allowed">
                        </div>

                        <div class="pt-2">
                            <button type="submit"
                                    class="inline-flex items-center justify-center px-5 py-2.5 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                <i class="fas fa-save mr-2"></i>Update Profile
                            </button>
                        </div>
                    </form>
                </div>

                <div class="lg:col-span-1 bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold text-gray-800 mb-6 border-b pb-3">Change Password</h3>
                    <form action="#" method="POST" class="space-y-6"> <div>
                            <label for="current_password" class="block text-sm font-medium text-gray-700">Current Password</label>
                            <input type="password" name="current_password" id="current_password" required
                                   class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="••••••••">
                        </div>

                        <div>
                            <label for="new_password" class="block text-sm font-medium text-gray-700">New Password</label>
                            <input type="password" name="new_password" id="new_password" required
                                   class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="••••••••">
                        </div>

                        <div>
                            <label for="confirm_new_password" class="block text-sm font-medium text-gray-700">Confirm New Password</label>
                            <input type="password" name="confirm_new_password" id="confirm_new_password" required
                                   class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="••••••••">
                        </div>

                        <div class="pt-2">
                            <button type="submit"
                                    class="inline-flex items-center justify-center w-full px-5 py-2.5 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                                <i class="fas fa-key mr-2"></i>Update Password
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
            &copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System. All rights reserved.
        </div>
    </footer>
    <script>
        // Basic mobile menu toggle
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    </script>
</body>
</html>
""",
    "404.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found (404) - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-100 flex flex-col items-center justify-center min-h-screen text-center px-4">
    <div class="max-w-md w-full">
        <img src="https://placehold.co/150x150/FF6347/FFFFFF?text=404" alt="404 Error Illustration" class="mx-auto mb-8 rounded-lg shadow-lg">
        <h1 class="text-6xl font-extrabold text-indigo-600">404</h1>
        <h2 class="mt-2 text-3xl font-bold text-gray-800">Page Not Found</h2>
        <p class="mt-4 text-gray-600">Oops! The page you're looking for doesn't seem to exist. It might have been moved, deleted, or you might have typed the address incorrectly.</p>
        <div class="mt-8">
            <a href="dashboard.html" 
               class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out">
                <i class="fas fa-home mr-2"></i>
                Go to Dashboard
            </a>
        </div>
        <p class="mt-10 text-sm text-gray-500">&copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System</p>
    </div>
</body>
</html>
""",
    "500.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Error (500) - USP Enrollment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-100 flex flex-col items-center justify-center min-h-screen text-center px-4">
    <div class="max-w-md w-full">
        <img src="https://placehold.co/150x150/FFA500/FFFFFF?text=500" alt="500 Error Illustration" class="mx-auto mb-8 rounded-lg shadow-lg">
        <h1 class="text-6xl font-extrabold text-red-600">500</h1>
        <h2 class="mt-2 text-3xl font-bold text-gray-800">Internal Server Error</h2>
        <p class="mt-4 text-gray-600">We're sorry, but something went wrong on our end. Our team has been notified and we're working to fix it.</p>
        <p class="mt-2 text-gray-600">Please try again later, or contact support if the problem persists.</p>
        <div class="mt-8">
            <a href="dashboard.html" 
               class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out">
                <i class="fas fa-arrow-left mr-2"></i>
                Back to Safety (Dashboard)
            </a>
        </div>
         <p class="mt-10 text-sm text-gray-500">&copy; <script>document.write(new Date().getFullYear())</script> USP Enrollment System</p>
    </div>
</body>
</html>
"""
}

def create_html_files():
    """
    Creates HTML files from the html_content dictionary.
    Each key in the dictionary will be a filename, and its value will be the content.
    """
    # Get the directory where the script is located
    # This ensures files are created in the same folder as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename, content in html_content.items():
        file_path = os.path.join(script_dir, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Successfully created {filename} at {file_path}")
        except IOError as e:
            print(f"Error writing file {filename}: {e}")

if __name__ == "__main__":
    # This will run when the script is executed
    print("Starting to create HTML files for USP Enrollment System UI...")
    create_html_files()
    print("All HTML files have been generated.")
    print(f"You can find them in the directory: {os.path.dirname(os.path.abspath(__file__))}")

