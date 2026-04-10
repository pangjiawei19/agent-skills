# BGP Billing 测试技术参考

本文档提供测试框架、依赖、配置等技术细节。

## 1. 技术栈

### 1.1 测试框架

```groovy
// build.gradle 中的测试依赖
testImplementation('org.springframework.boot:spring-boot-starter-test')
testImplementation 'io.projectreactor:reactor-test'
testImplementation 'org.mockito:mockito-inline:5.2.0'  // 用于 Mock 静态方法
```

> **注意**: `spring-boot-starter-test` 已包含 `mockito-core` 和 `assertj-core`,无需重复添加

### 1.2 核心工具类

| 工具 | 用途 | 使用场景 |
|-----|------|---------|
| `Mockito` | Mock 依赖对象 | 单元测试中隔离外部依赖 |
| `StepVerifier` | 验证响应式流 | 测试 `Mono`/`Flux` 返回值 |
| `WebTestClient` | HTTP 接口测试 | Controller 集成测试 |
| `AssertJ` | 流式断言 | 所有测试的断言 |

## 2. 测试基类

### 2.1 BaseUnitTest

单元测试基类,不启动 Spring 容器:

```java
package com.mt.billing;

import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

/**
 * 单元测试基类
 *
 * 特点:
 * - 不启动 Spring 容器,执行速度快
 * - 使用 Mockito 进行依赖隔离
 * - 适用于 Service、Util、Handler 等层的单元测试
 */
@ExtendWith(MockitoExtension.class)
public abstract class BaseUnitTest {

    /**
     * 创建一个用于测试的 Reactor Context
     */
    protected reactor.util.context.Context createTestContext(Integer appId) {
        return reactor.util.context.Context.of("appId", appId);
    }
}
```

### 2.2 BaseIntegrationTest

集成测试基类,启动 Spring 容器:

```java
package com.mt.billing;

import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;

/**
 * 集成测试基类
 *
 * 重要规则:
 * - 所有集成测试类必须继承此基类
 * - 所有 @MockBean 必须定义在此基类中,禁止在子类中使用 @MockBean
 * - 这样可以确保所有集成测试共享同一个 Spring 上下文
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient(timeout = "60s")
@ActiveProfiles("test")
public abstract class BaseIntegrationTest {

    // ========== 所有需要 Mock 的外部依赖都定义在这里 ==========

    /**
     * Mock 外部 RPC 服务示例
     * 子类可以通过 when(...).thenReturn(...) 设置 Mock 行为
     */
    // @MockBean
    // protected GoogleValidateRpc googleValidateRpc;

    // @MockBean
    // protected TrackerUtil trackerUtil;

    // 根据实际需要添加其他 @MockBean...
}
```

### 2.3 关于 @MockBean 的重要警告

⚠️ **禁止在集成测试子类中使用 `@MockBean`**

本项目使用了 `ApplicationContextHelper` 持有静态的 `ApplicationContext`。如果在不同测试类中使用不同的 `@MockBean` 组合,Spring Test 会创建多个上下文,导致静态变量被覆盖,测试随机失败。

**规则:**

1. 所有集成测试类必须继承 `BaseIntegrationTest`
2. 所有 `@MockBean` 必须定义在 `BaseIntegrationTest` 基类中
3. 子类只能使用基类中已定义的 MockBean,不能添加新的

```java
// ❌ 禁止:在子类中使用 @MockBean
class SomeIntegrationTest extends BaseIntegrationTest {
    @MockBean  // 禁止!会导致创建新的上下文
    private SomeService someService;
}

// ✅ 正确:使用基类中已定义的 MockBean
class SomeIntegrationTest extends BaseIntegrationTest {
    // 直接使用基类中的 protected MockBean 字段

    @Test
    void someTest() {
        when(googleValidateRpc.requestVerify(...)).thenReturn(...);
    }
}
```

## 3. TestRequestHelper 使用说明

`TestRequestHelper` 是项目封装的 HTTP 请求工具类,自动处理 `appId` 和 `sign` header。

### 3.1 基本使用

```java
// 发送 POST 请求,期望 200 响应
MTResponse<ValidateRespDto> response = TestRequestHelper.postToServerWithJsonForOK(
    "/billing/payment/verify",  // 完整路径
    request,                     // 请求体
    Map.of(),                    // 额外的 headers(可选)
    ValidateRespDto.class        // 响应类型
);

// 发送 POST 请求,期望错误响应
TestRequestHelper.postToServerWithJsonForError(
    "/billing/payment/verify",
    request,
    Map.of(),
    403  // 期望的错误状态码
);
```

### 3.2 自定义 Headers

```java
// 覆盖默认的 appId
Map<String, String> customHeaders = Map.of("appId", "");
TestRequestHelper.postToServerWithJsonForError(
    "/billing/payment/verify",
    request,
    customHeaders,
    403
);
```

### 3.3 处理 List 响应

```java
// 获取原始响应字符串
String responseBody = TestRequestHelper.postToServerWithJsonForOK(
    "/billing/payment/finish",
    request,
    Map.of(),
    String.class
);

// 手动解析 List 响应
MTResponse<List<String>> mtResponse = JsonUtil.parse(responseBody, MTResponse.class, List.class);
List<String> data = mtResponse.getData();
```

## 4. 常见问题解决方案

### 4.1 测试响应式代码时的 Context 传递

```java
// 涉及使用 StoreUtil 的测试,要在 Context 中设置 CONTEXT_STORE_KEY
StepVerifier.create(
    service.methodThatUsesContext()
            .contextWrite(ctx -> StoreUtil.set(ctx, "purchaseTokenData", testPurchaseTokenData))
            .contextWrite(ctx -> ctx.put(CONTEXT_STORE_KEY, Maps.newConcurrentMap()))
)
.assertNext(result -> {
    assertThat(result).isNotNull();
})
.verifyComplete();
```

### 4.2 测试异步调用

```java
@Test
@DisplayName("当发送回调成功时,应正常完成")
void completesSuccessfully_whenCallbackSendsSuccessfully() {
    // Given
    when(sqsTemplate.sendAsync(any())).thenReturn(CompletableFuture.completedFuture(null));

    // When & Then - 使用 Schedulers.immediate() 处理异步调用
    StepVerifier.create(
        service.sendCallback(payment)
            .subscribeOn(Schedulers.immediate())
    )
    .verifyComplete();
}
```

### 4.3 Mock 重载方法时的类型匹配

当 Mock 的方法有多个重载版本时,使用明确的类型匹配:

```java
// ✅ 正确:明确指定每个参数的类型
try (MockedStatic<ReactiveHttpClient> mockedHttpClient = mockStatic(ReactiveHttpClient.class)) {
    mockedHttpClient.when(() -> ReactiveHttpClient.postBody(
            anyString(),                    // String url
            any(Object.class),              // Object body
            any(java.util.Map.class),       // Map<String, String> headers
            eq(String.class)))              // Class<T> responseType
            .thenReturn(Mono.just("success"));
}
```

### 4.4 @Builder 注解 DTO 的序列化问题

使用 `@Builder` 注解的类,需要添加构造函数注解:

```java
@Builder
@Data
@NoArgsConstructor      // 添加无参构造函数
@AllArgsConstructor    // 添加全参构造函数
public class CallbackBillingInfoDto {
    private String channel;
    private String paymentId;
}
```

### 4.5 响应式流中的 mapNotNull 陷阱

`mapNotNull` 操作符如果返回 null,会导致流变为空:

```java
// ✅ 正确:返回有效的对象
InAppPurchase.InAppPurchasePriceUnit priceUnit = new InAppPurchase.InAppPurchasePriceUnit();
priceUnit.setPrice("9.99");
when(inAppPurchaseService.getPriceUnit(any(), anyString(), anyInt(), anyString()))
    .thenReturn(priceUnit);  // 返回非 null 值
```

### 4.6 Mock 参数匹配的灵活性

优先使用灵活的匹配器:

```java
// ✅ 正确:使用 any() 等灵活匹配器
when(service.createOrder(anyString()))  // 匹配任何字符串
    .thenReturn(Mono.just(order));

// ✅ 如果只需要验证参数不为空
when(service.createOrder(argThat(id -> id != null && !id.isBlank())))
    .thenReturn(Mono.just(order));

// ✅ 仅在需要精确匹配时使用 eq()
when(service.getById(eq(1203)))  // 明确知道参数值
    .thenReturn(Mono.just(appInfo));
```

### 4.7 静态方法 Mock 的时机问题

如果静态方法在被测方法执行前就被调用,Mock 必须覆盖整个测试方法:

```java
// ✅ 正确:MockedStatic 覆盖整个测试方法
@Test
void createsPaymentLinkSuccessfully() {
    // Given
    try (MockedStatic<PaymentUtil> mockedPaymentUtil = mockStatic(PaymentUtil.class);
         MockedStatic<DateTimeUtil> mockedDateTimeUtil = mockStatic(DateTimeUtil.class)) {

        // 在调用被测方法之前设置 Mock
        mockedPaymentUtil.when(PaymentUtil::newBillingOrderId).thenReturn("order-123");
        mockedDateTimeUtil.when(DateTimeUtil::currentSeconds).thenReturn(1609459200);

        // 设置其他依赖的 Mock
        when(rpcService.create(anyString(), any())).thenReturn(Mono.just(response));

        // When & Then
        StepVerifier.create(service.createPaymentLink(appId, request))
            .assertNext(result -> {
                assertThat(result.getOrderId()).isEqualTo("order-123");
            })
            .verifyComplete();
    }
}
```

### 4.8 测试数据完整性

确保测试数据完整,特别是嵌套对象:

```java
// ✅ 正确:完整的测试数据
InAppPurchase iap = new InAppPurchase();
iap.setSku("com.example.product");
iap.setAppId(1203);

// 必须包含所有会被访问的嵌套对象
InAppPurchase.InAppPurchasePrices prices = new InAppPurchase.InAppPurchasePrices();
InAppPurchase.InAppPurchasePriceUnit defaultPrice = new InAppPurchase.InAppPurchasePriceUnit();
defaultPrice.setPrice("9.99");
defaultPrice.setCurrency("USD");
prices.setDefaultPrice(defaultPrice);
iap.setPrices(prices);
```

### 4.9 ReactiveHttpClient Mock

`ReactiveHttpClient` 是静态方法,需要同时 Mock `ApplicationContextHelper`:

```java
try (MockedStatic<ApplicationContextHelper> mockedHelper = mockStatic(ApplicationContextHelper.class);
     MockedStatic<ReactiveHttpClient> mockedHttpClient = mockStatic(ReactiveHttpClient.class)) {

    // Mock ApplicationContextHelper.getBean() 用于获取 WebClient
    mockedHelper.when(() -> ApplicationContextHelper.getBean(any(Class.class)))
            .thenReturn(mock(WebClient.class));

    // Mock ReactiveHttpClient.postBody() 静态方法
    mockedHttpClient.when(() -> ReactiveHttpClient.postBody(
                    anyString(),
                    any(Object.class),
                    any(java.util.Map.class),
                    eq(String.class)))
            .thenReturn(Mono.just("success"));
}
```

### 4.10 TrackerUtil.sendTrack 返回值语义

**重要业务逻辑**: `TrackerUtil.sendTrack()` 的返回值有特殊语义:

- **成功时返回 `Mono.empty()`** - 没有返回值,表示发送成功
- **失败时返回有值的 `Mono<String>`** - 返回错误信息字符串,表示发送失败

```java
// 成功场景
when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
        .thenReturn(Mono.empty());

// 失败场景
when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
        .thenReturn(Mono.just("error: connection timeout"));
```

## 5. 测试文件组织

```
src/test/java/com/mt/billing/
├── service/
│   ├── PaymentGoogleServiceTest.java          # 单元测试
│   ├── PaymentGoogleServiceIntegrationTest.java  # 集成测试
│   └── assist/
│       ├── GoogleValidateServiceTest.java
│       └── AppleValidateServiceTest.java
├── controller/
│   ├── VerifyControllerIntegrationTest.java
│   └── InAppPurchaseControllerIntegrationTest.java
├── filters/
│   ├── AppCheckFilterIntegrationTest.java
│   └── SignatureFilterIntegrationTest.java
├── aspect/
│   └── BillingDataVersionIncreaseAspectTest.java
├── sqs/
│   ├── TrackMessageHandlerTest.java
│   └── AdjustMessageHandlerTest.java
├── util/
│   ├── TrackerUtilTest.java
│   └── PaymentUtilTest.java
└── testdata/
    └── TestDataFactory.java                    # 测试数据工厂
```

## 6. 测试覆盖率要求

| 层级 | 行覆盖率 | 分支覆盖率 | 说明 |
|-----|---------|-----------|------|
| Service | ≥ 80% | ≥ 70% | 核心业务逻辑必须充分测试 |
| Controller | ≥ 70% | ≥ 60% | 主要路径必须覆盖 |
| Util | ≥ 90% | ≥ 80% | 工具类应有高覆盖率 |
| DAO | ≥ 60% | - | 通过集成测试覆盖 |

## 7. CI 配置

```yaml
# .gitlab-ci.yml 中的测试阶段
test:
  stage: test
  script:
    - ./gradlew test
  variables:
    IsCi: "true"
```

## 8. 测试配置文件

### 8.1 application-test.yml

```yaml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
  r2dbc:
    url: r2dbc:h2:mem:///testdb
```

### 8.2 测试环境变量

```properties
# 测试环境特定配置
spring.profiles.active=test
```
