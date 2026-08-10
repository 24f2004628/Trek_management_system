const { createApp } = Vue;


createApp({

    data() {

        return {

            treks: [],

            bookings: [],

            user: null,

            search: "",

            difficulty: "",

            showLogin: false,

            loginForm: {
                email: "",
                password: ""
            },

            message: "",

            messageType: "success",

            loading: false

        };

    },


    mounted() {

        this.checkUser();

        this.loadTreks();

    },


    methods: {

        // ==========================================
        // API REQUEST HELPER
        // ==========================================

        async api(url, options = {}) {

            const response = await fetch(url, {

                credentials: "same-origin",

                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },

                ...options

            });

            const data = await response.json();

            if (!response.ok) {

                throw new Error(
                    data.error || "Something went wrong"
                );

            }

            return data;

        },


        // ==========================================
        // CHECK LOGIN
        // ==========================================

        async checkUser() {

            try {

                const data =
                    await this.api("/api/me");

                if (data.authenticated) {

                    this.user = data.user;

                    await this.loadBookings();

                }

            } catch (error) {

                console.error(error);

            }

        },


        // ==========================================
        // LOAD TREKS
        // ==========================================

        async loadTreks() {

            try {

                let url = "/api/treks?";

                if (this.search) {

                    url +=
                        "q=" +
                        encodeURIComponent(this.search) +
                        "&";

                }

                if (this.difficulty) {

                    url +=
                        "difficulty=" +
                        encodeURIComponent(this.difficulty) +
                        "&";

                }

                const data =
                    await this.api(url);

                this.treks = data.treks;

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // LOGIN
        // ==========================================

        async login() {

            if (
                !this.loginForm.email ||
                !this.loginForm.password
            ) {

                this.showMessage(
                    "Enter email and password",
                    "warning"
                );

                return;

            }

            try {

                const data =
                    await this.api(
                        "/api/auth/login",
                        {
                            method: "POST",

                            body: JSON.stringify(
                                this.loginForm
                            )
                        }
                    );

                this.user = data.user;

                this.showLogin = false;

                this.loginForm = {
                    email: "",
                    password: ""
                };

                this.showMessage(
                    "Login successful!",
                    "success"
                );

                await this.loadBookings();

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // LOGOUT
        // ==========================================

        async logout() {

            try {

                await this.api(
                    "/api/auth/logout",
                    {
                        method: "POST"
                    }
                );

                this.user = null;

                this.bookings = [];

                this.showMessage(
                    "Logged out successfully",
                    "success"
                );

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // BOOK TREK
        // ==========================================

        async bookTrek(trekId) {

            if (!this.user) {

                this.showLogin = true;

                this.showMessage(
                    "Please login before booking",
                    "warning"
                );

                return;

            }

            try {

                await this.api(
                    `/api/treks/${trekId}/book`,
                    {
                        method: "POST"
                    }
                );

                this.showMessage(
                    "Trek booked successfully!",
                    "success"
                );

                await this.loadTreks();

                await this.loadBookings();

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // BOOKINGS
        // ==========================================

        async loadBookings() {

            if (!this.user) {

                return;

            }

            try {

                const data =
                    await this.api(
                        "/api/bookings"
                    );

                this.bookings =
                    data.bookings;

            } catch (error) {

                console.error(error);

            }

        },
        // ==========================================
        // EXPORT BOOKING HISTORY
        // ==========================================

        async exportBookings() {

            try {

                const data = await this.api(
                    "/api/bookings/export",
                    {
                        method: "POST"
                    }
                );

                this.showMessage(
                    "Export started. Your booking history is being generated.",
                    "success"
                );

                console.log(
                    "Celery Task ID:",
                    data.task_id
                );

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },

        // ==========================================
        // FILTER RESET
        // ==========================================

        resetFilters() {

            this.search = "";

            this.difficulty = "";

            this.loadTreks();

        },


        // ==========================================
        // UI HELPERS
        // ==========================================

        showMessage(message, type) {

            this.message = message;

            this.messageType = type;

            setTimeout(() => {

                this.message = "";

            }, 3000);

        },


        difficultyBadge(difficulty) {

            if (difficulty === "Easy") {

                return "bg-success";

            }

            if (difficulty === "Medium") {

                return "bg-warning text-dark";

            }

            if (difficulty === "Hard") {

                return "bg-danger";

            }

            return "bg-secondary";

        },


        formatDate(date) {

            if (!date) {

                return "-";

            }

            return new Date(date)
                .toLocaleDateString();

        }

    }

}).mount("#app");