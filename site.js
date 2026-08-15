(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const internalLinks = document.querySelectorAll('a[href^="#"]');

  internalLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
      window.history.replaceState(null, "", link.getAttribute("href"));
    });
  });

  if (reduceMotion || !window.gsap || !window.ScrollTrigger) return;

  gsap.registerPlugin(ScrollTrigger);
  gsap.defaults({ overwrite: "auto" });

  const media = gsap.matchMedia();

  media.add(
    {
      animate: "(prefers-reduced-motion: no-preference)",
      desktop: "(min-width: 681px)"
    },
    ({ conditions }) => {
      const travel = conditions.desktop ? 34 : 22;

      gsap.timeline({ defaults: { duration: 0.82, ease: "power3.out" } })
        .from(".brand", { autoAlpha: 0, y: -18 })
        .from("[data-intro-group] > *", { autoAlpha: 0, y: travel, stagger: 0.11 }, "-=0.42");

      gsap.utils.toArray("[data-reveal]").forEach((element) => {
        gsap.fromTo(
          element,
          { autoAlpha: 0, y: travel },
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.78,
            ease: "power3.out",
            scrollTrigger: {
              trigger: element,
              start: "top 88%",
              end: "bottom 14%",
              toggleActions: "play none none reverse"
            }
          }
        );
      });

      gsap.fromTo(
        "[data-reveal-group] > *",
        { autoAlpha: 0, y: travel },
        {
          autoAlpha: 1,
          y: 0,
          duration: 0.72,
          stagger: 0.08,
          ease: "power3.out",
          scrollTrigger: {
            trigger: "[data-reveal-group]",
            start: "top 84%",
            end: "bottom 12%",
            toggleActions: "play none none reverse"
          }
        }
      );

      gsap.to('[data-parallax="hero"]', {
        yPercent: 8,
        scale: 1.035,
        ease: "none",
        scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: 0.6 }
      });

      gsap.fromTo(
        '[data-parallax="closing"]',
        { yPercent: -5, scale: 1.04 },
        {
          yPercent: 5,
          ease: "none",
          scrollTrigger: { trigger: ".closing", start: "top bottom", end: "bottom top", scrub: 0.65 }
        }
      );

      gsap.to(".scroll-progress span", {
        scaleX: 1,
        ease: "none",
        scrollTrigger: { start: 0, end: "max", scrub: 0.15 }
      });
    }
  );

  window.addEventListener("load", () => ScrollTrigger.refresh(), { once: true });
})();
