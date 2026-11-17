FROM eclipse-temurin:17-jre
WORKDIR /app
RUN addgroup --system --gid 10001 appgroup && adduser --system --uid 10001 --ingroup appgroup appuser
COPY --chown=appuser:appgroup target/*.jar app.jar
USER 10001
EXPOSE 8082
ENTRYPOINT [ "java","-jar","app.jar" ]
