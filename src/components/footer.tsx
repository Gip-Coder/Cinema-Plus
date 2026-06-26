export function Footer() {
  return (
    <footer className="w-full border-t border-border/40 py-6 md:py-8 bg-background">
      <div className="container flex flex-col items-center justify-between gap-4 px-4 md:px-8 text-center md:flex-row max-w-7xl mx-auto text-sm text-muted-foreground">
        <p className="leading-5">
          &copy; {new Date().getFullYear()} Cinema Plus. All rights reserved. Built with Next.js & FastAPI.
        </p>
        <div className="flex gap-4">
          <a href="#" className="hover:underline transition-colors hover:text-foreground">
            Privacy Policy
          </a>
          <a href="#" className="hover:underline transition-colors hover:text-foreground">
            Terms of Service
          </a>
        </div>
      </div>
    </footer>
  );
}
