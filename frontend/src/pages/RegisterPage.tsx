import { AuthForm } from "../widgets/auth/AuthForm";
import styles from "../styles/pages/RegisterPage.module.css";

type Props = {
  onSubmit: (payload: {
    login: string;
    password: string;
    passwordConfirm: string;
    name: string;
    username?: string;
    email?: string;
  }) => void;
  onGoogleAuth?: () => Promise<void> | void;
  googleAuthDisabledReason?: string | null;
  onNavigate: (path: string) => void;
  error?: string | null;
  passwordRules?: string[];
};

export function RegisterPage({
  onSubmit,
  onGoogleAuth,
  googleAuthDisabledReason = null,
  onNavigate,
  error = null,
  passwordRules = [],
}: Props) {
  return (
    <AuthForm
      mode="register"
      title="Регистрация"
      submitLabel="Создать аккаунт"
      onSubmit={(payload) => {
        if ("identifier" in payload) return;
        onSubmit(payload);
      }}
      onGoogleAuth={onGoogleAuth}
      googleAuthDisabledReason={googleAuthDisabledReason}
      onNavigate={onNavigate}
      error={error}
      passwordRules={passwordRules}
      className={styles.page}
    />
  );
}
