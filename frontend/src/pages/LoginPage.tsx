import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { login, fetchMe } from "../features/auth/api";
import { useAuthStore } from "../features/auth/store";
import { ApiError } from "../services/httpClient";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});
type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const setUser = useAuthStore((s) => s.setUser);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      const tokens = await login(values);
      setSession(tokens);
      const user = await fetchMe();
      setUser(user);
      navigate("/");
    } catch (err) {
      if (err instanceof ApiError) setFormError(err.message);
      else setFormError("Something went wrong. Please try again.");
    }
  }

  return (
    <div className="form-card">
      <h1 className="form-title">Welcome back</h1>
      <p className="form-sub">Log in to your VK paper trading account.</p>

      {formError && <div className="form-banner-error">{formError}</div>}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="email" {...register("email")} />
          {errors.email && <div className="form-error">{errors.email.message}</div>}
        </div>
        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" {...register("password")} />
          {errors.password && <div className="form-error">{errors.password.message}</div>}
        </div>
        <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <div className="form-footer">
        New here? <Link to="/register">Create an account</Link>
      </div>
    </div>
  );
}
