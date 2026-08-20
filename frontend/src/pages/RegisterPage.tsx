import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { register as registerAccount, login, fetchMe } from "../features/auth/api";
import { useAuthStore } from "../features/auth/store";
import { ApiError } from "../services/httpClient";

const schema = z.object({
  displayName: z.string().min(1, "Display name is required").max(120),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const setUser = useAuthStore((s) => s.setUser);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register: registerField,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await registerAccount({
        email: values.email,
        password: values.password,
        display_name: values.displayName,
      });
      const tokens = await login({ email: values.email, password: values.password });
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
      <h1 className="form-title">Create your account</h1>
      <p className="form-sub">
        You'll start with a ₹1,00,000 simulated balance. No real money, ever.
      </p>

      {formError && <div className="form-banner-error">{formError}</div>}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="form-field">
          <label htmlFor="displayName">Display name</label>
          <input id="displayName" type="text" autoComplete="name" {...registerField("displayName")} />
          {errors.displayName && <div className="form-error">{errors.displayName.message}</div>}
        </div>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="email" {...registerField("email")} />
          {errors.email && <div className="form-error">{errors.email.message}</div>}
        </div>
        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="new-password" {...registerField("password")} />
          {errors.password && <div className="form-error">{errors.password.message}</div>}
        </div>
        <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <div className="form-footer">
        Already have an account? <Link to="/login">Log in</Link>
      </div>
    </div>
  );
}
